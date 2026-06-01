# training/evaluation/walk_forward.py

import numpy as np
import torch
from typing import Dict, Type, Any
import sys
sys.path.append('.')

from training.evaluation.metrics import Metrics
from training.evaluation.backtester import Backtester


class WalkForwardValidator:
    """
    Performs walk-forward validation by splitting data into train/test portions.
    Model is trained on train portion, tested on unseen test portion.
    """
    
    def __init__(self, feature_matrix: np.ndarray, train_size: float = None, test_size: float = None):
        """
        Initialize walk-forward validator.
        
        Args:
            feature_matrix: Numpy array of shape (n_steps, n_features)
            train_size: Fraction of data for training (default: 0.7)
            test_size: Fraction of data for testing (default: 0.3)
        """
        self.feature_matrix = feature_matrix
        self.n_samples = len(feature_matrix)
        
        # Set defaults
        if train_size is None and test_size is None:
            train_size = 0.7
            test_size = 0.3
        elif train_size is None:
            train_size = 1.0 - test_size
        elif test_size is None:
            test_size = 1.0 - train_size
        
        # Validate sizes
        if abs(train_size + test_size - 1.0) > 0.001:
            raise ValueError(f"train_size + test_size must equal 1.0, got {train_size} + {test_size} = {train_size + test_size}")
        
        self.train_size = train_size
        self.test_size = test_size
        
        # Calculate split indices
        self.split_idx = int(self.n_samples * self.train_size)
        
        if self.split_idx == 0 or self.split_idx >= self.n_samples:
            raise ValueError(f"Invalid split: train_size={train_size} gives {self.split_idx} samples")
    
    def run(self, trainer_class: Type, model_class: Type) -> Dict:
        """
        Run walk-forward validation.
        
        Args:
            trainer_class: Class used to train models (must accept feature_matrix in __init__)
            model_class: Class of model to instantiate (must accept input_dim parameter)
            
        Returns:
            Metrics dictionary from evaluating on test portion only
        """
        # Split data into train and test
        train_features = self.feature_matrix[:self.split_idx]
        test_features = self.feature_matrix[self.split_idx:]
        
        # Determine input dimension from feature matrix
        input_dim = self.feature_matrix.shape[1]
        
        # Initialize model
        model = model_class(input_dim=input_dim)
        
        # Initialize trainer with training data - using the existing Trainer class pattern
        trainer = trainer_class(feature_matrix=train_features)
        
        # Train the model
        trained_model = trainer.train()
        
        # Run backtester on test portion only
        backtester = Backtester(test_features)
        trades = backtester.run(trained_model)
        
        # Calculate metrics
        metrics_calculator = Metrics()
        results = metrics_calculator.calculate(trades)
        
        # Add metadata
        results['train_samples'] = len(train_features)
        results['test_samples'] = len(test_features)
        results['total_trades_backtest'] = len(trades)
        
        return results
    
    def run_expanding_window(self, trainer_class: Type, model_class: Type, n_splits: int = 5) -> Dict:
        """
        Run expanding window walk-forward validation.
        
        Args:
            trainer_class: Class used to train models (must accept feature_matrix in __init__)
            model_class: Class of model to instantiate (must accept input_dim parameter)
            n_splits: Number of validation splits
            
        Returns:
            Dictionary with average metrics across all splits
        """
        all_metrics = []
        
        min_train_size = self.split_idx
        step_size = (self.n_samples - min_train_size) // n_splits
        
        for split in range(n_splits):
            # Expanding window
            current_train_end = min_train_size + (split * step_size)
            current_test_end = min(current_train_end + step_size, self.n_samples)
            
            if current_test_end - current_train_end < 10:
                break
            
            # Split data
            train_features = self.feature_matrix[:current_train_end]
            test_features = self.feature_matrix[current_train_end:current_test_end]
            
            # Create temporary validator for this split
            temp_validator = WalkForwardValidator.__new__(WalkForwardValidator)
            temp_validator.feature_matrix = self.feature_matrix
            temp_validator.train_size = len(train_features) / self.n_samples
            temp_validator.test_size = len(test_features) / self.n_samples
            temp_validator.n_samples = self.n_samples
            temp_validator.split_idx = current_train_end
            
            # Run validation
            try:
                metrics = temp_validator.run(trainer_class, model_class)
                all_metrics.append(metrics)
            except Exception as e:
                print(f"Split {split} failed: {e}")
                continue
        
        # Average metrics across splits
        if not all_metrics:
            return {}
        
        averaged_metrics = {
            'win_rate': np.mean([m['win_rate'] for m in all_metrics]),
            'profit_factor': np.mean([m['profit_factor'] for m in all_metrics if m['profit_factor'] != float('inf')]),
            'max_drawdown': np.mean([m['max_drawdown'] for m in all_metrics]),
            'total_pnl': np.mean([m['total_pnl'] for m in all_metrics]),
            'sharpe_ratio': np.mean([m['sharpe_ratio'] for m in all_metrics]),
            'total_trades': np.sum([m['total_trades'] for m in all_metrics]),
            'consecutive_losses': np.max([m['consecutive_losses'] for m in all_metrics]),
            'n_splits': len(all_metrics),
            'split_results': all_metrics
        }
        
        return averaged_metrics