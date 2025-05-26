import numpy as np
import pandas as pd
from scipy.optimize import minimize

class AccelerometerCalibrator:
    """
    A class for calibrating triaxial accelerometer data.
    
    This class provides methods for:
    - Converting m/s² to g
    - Computing vector magnitudes
    - Identifying static windows
    - Auto-calibrating accelerometer data
    - Applying calibration corrections
    """
    
    def __init__(self, axis_cols=('x', 'y', 'z'), fs=100, static_threshold=0.013, unit='m/s2'):
        """
        Initialize the AccelerometerCalibrator.

        Parameters:
            axis_cols (tuple): Names of accelerometer columns (x, y, z)
            fs (int): Sampling frequency in Hz
            static_threshold (float): Standard deviation threshold to detect static periods (in g)
            unit (str): Unit of the input data ('m/s2' or 'g')
        """
        self.axis_cols = axis_cols
        self.fs = fs
        self.static_threshold = static_threshold
        self.unit = unit
        self.gains = None
        self.offsets = None
        self.converted_to_g = False

    def convert_to_g(self, df):
        """
        Convert accelerometer data from m/s² to g if needed.
        This should be called before any calibration steps.

        Parameters:
            df (pd.DataFrame): Input DataFrame with accelerometer data

        Returns:
            pd.DataFrame: DataFrame with data converted to g

        Raises:
            ValueError: If data is already in g or unit is not recognized
        """
        if self.converted_to_g:
            return df

        if self.unit not in ['m/s2', 'g']:
            raise ValueError("Unit must be either 'm/s2' or 'g'")

        if self.unit == 'g':
            self.converted_to_g = True
            return df

        # Create a copy to avoid modifying original data
        df_converted = df.copy()
        
        # Convert m/s² to g by dividing by 9.81
        for axis in self.axis_cols:
            mask = df[axis] != -9999  # Preserve invalid values
            df_converted.loc[mask, axis] = df.loc[mask, axis] / 9.81

        self.converted_to_g = True
        return df_converted

    def vector_magnitude(self, df):
        """
        Compute vector magnitude of triaxial acceleration data.

        Parameters:
            df (pd.DataFrame): Input DataFrame

        Returns:
            np.ndarray: Vector magnitude for each row
        """
        x, y, z = self.axis_cols
        return np.sqrt(df[x]**2 + df[y]**2 + df[z]**2)

    def select_static_windows(self, df, window_size=10):
        """
        Identify static (non-movement) windows based on low standard deviation and no invalid flags.

        Parameters:
            df (pd.DataFrame): Input DataFrame
            window_size (int): Duration of each window in seconds

        Returns:
            np.ndarray: Static window means (Nx3)
        """
        n = int(window_size * self.fs)
        static_means = []

        for i in range(0, len(df) - n + 1, n):
            window = df.iloc[i:i+n]
            if (window[list(self.axis_cols)] == -9999).any().any():
                continue
            stds = window[list(self.axis_cols)].std()
            if all(stds < self.static_threshold):
                static_means.append(window[list(self.axis_cols)].mean().values)

        return np.array(static_means)

    def _icp_calibration_step(self, params, data):
        """
        Single step of ICP-like calibration process.
        For each static window, find the closest point on the unit sphere
        and update parameters to minimize the distance.

        Parameters:
            params (list): [a_x, a_y, a_z, d_x, d_y, d_z]
            data (np.ndarray): Nx3 static windows

        Returns:
            tuple: (updated_params, error)
        """
        a = np.array(params[0:3])  # gains
        d = np.array(params[3:6])  # offsets
        
        # Apply current calibration
        calibrated = (data - d) * a
        
        # For each point, find closest point on unit sphere
        # This is done by normalizing the vector
        target_points = calibrated / np.linalg.norm(calibrated, axis=1)[:, np.newaxis]
        
        # Solve for new parameters that minimize distance to target points
        # This is a linear least squares problem for each axis
        new_params = np.zeros(6)
        
        for i in range(3):  # For each axis
            # Solve: (data_i - d_i) * a_i = target_i
            # Rearranged: data_i * a_i - d_i * a_i = target_i
            # This is linear in a_i and d_i
            A = np.column_stack([data[:, i], -np.ones_like(data[:, i])])
            b = target_points[:, i]
            x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
            new_params[i] = x[0]    # gain
            new_params[i+3] = x[1]  # offset
        
        # Calculate error as mean distance to unit sphere
        new_calibrated = (data - new_params[3:6]) * new_params[0:3]
        norms = np.linalg.norm(new_calibrated, axis=1)
        error = np.mean(np.abs(norms - 1.0))
        
        return new_params, error

    def calibrate(self, df, max_iterations=50, tolerance=1e-6):
        """
        Estimate gain and offset for each axis using ICP-like optimization.
        Input data is converted to g before calibration.

        Parameters:
            df (pd.DataFrame): Input DataFrame in m/s² or g
            max_iterations (int): Maximum number of ICP iterations
            tolerance (float): Convergence tolerance

        Returns:
            tuple: (gains, offsets) each as list of 3 floats, in g units

        Raises:
            ValueError: If not enough valid static windows are found
        """
        # Convert input data to g before calibration
        df_g = self.convert_to_g(df)
        
        df_filtered = df_g[list(self.axis_cols)].replace(-9999, np.nan).dropna()
    
        self.diagnose_static_windows(df_filtered, window_size=10, verbose=True)
        static_data = self.select_static_windows(df_filtered)

        if len(static_data) < 10:
            raise ValueError("Not enough valid static windows for calibration.")

        # Start with ideal parameters
        current_params = np.array([1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
        current_error = float('inf')
        
        # ICP iteration
        for iteration in range(max_iterations):
            # Single ICP step
            new_params, new_error = self._icp_calibration_step(current_params, static_data)
            
            # Check convergence
            if abs(new_error - current_error) < tolerance:
                break
                
            current_params = new_params
            current_error = new_error
            
            # Apply bounds
            # Gains: 0.98 to 1.02
            current_params[0:3] = np.clip(current_params[0:3], 0.98, 1.02)
            # Offsets: -0.05 to 0.05
            current_params[3:6] = np.clip(current_params[3:6], -0.05, 0.05)

        self.gains = current_params[0:3].tolist()
        self.offsets = current_params[3:6].tolist()

        # Print calibration results
        print(f"\nCalibration Results (after {iteration + 1} iterations):")
        print(f"Gains: {[f'{g:.4f}' for g in self.gains]} (should be close to 1.0)")
        print(f"Offsets: {[f'{o:.4f}' for o in self.offsets]} (should be close to 0.0)")
        
        # Calculate and print final errors
        calibrated = (static_data - self.offsets) * self.gains
        norms = np.linalg.norm(calibrated, axis=1)
        
        print("\nCalibration Statistics:")
        print(f"Mean magnitude: {np.mean(norms):.4f} (should be close to 1.0)")
        print(f"Std magnitude: {np.std(norms):.4f} (should be small)")
        print(f"Gain deviation from 1.0: {[f'{abs(g-1.0):.4f}' for g in self.gains]}")
        print(f"Offset deviation from 0.0: {[f'{abs(o):.4f}' for o in self.offsets]}")
        print(f"Final error: {current_error:.6f}")
        self.converted_to_g = False

        return self.gains, self.offsets

    def apply_calibration(self, df):
        """
        Apply gain and offset correction to accelerometer data.
        Input data is converted to g before applying calibration.

        Parameters:
            df (pd.DataFrame): Original DataFrame in m/s² or g

        Returns:
            pd.DataFrame: Calibrated DataFrame in g units

        Raises:
            ValueError: If calibration parameters haven't been computed yet
        """
        if self.gains is None or self.offsets is None:
            raise ValueError("Calibration parameters not found. Run calibrate() first.")

        # Convert input data to g before applying calibration
        print("Original data:")
        print(df.head())
        df_g = self.convert_to_g(df)
        print("Converted data:")
        print(df_g.head())
        df_calibrated = df_g.copy()

        for i, axis in enumerate(self.axis_cols):
            mask = df_g[axis] != -9999
            df_calibrated.loc[mask, axis] = (df_g.loc[mask, axis] - self.offsets[i]) * self.gains[i]

        print("Calibrated data:")
        df_calibrated.head()    
        return df_calibrated

    def get_calibration_parameters(self):
        """
        Get the current calibration parameters.

        Returns:
            tuple: (gains, offsets) each as list of 3 floats, or (None, None) if not calibrated
        """
        return self.gains, self.offsets

    def diagnose_static_windows(self, df, window_size=10, verbose=True):
        """
        Diagnostic method to understand static window detection.

        Parameters:
            df (pd.DataFrame): Input DataFrame
            window_size (int): Duration of each window in seconds
            verbose (bool): Whether to print detailed information

        Returns:
            dict: Diagnostic information including:
                - total_windows: Total number of windows checked
                - valid_windows: Number of windows without invalid values
                - static_windows: Number of windows that passed the static test
                - window_stds: Standard deviations of all valid windows
        """
        n = int(window_size * self.fs)
        total_windows = (len(df) - n + 1) // n
        valid_windows = 0
        static_windows = 0
        window_stds = []
        static_windows_stds = []

        for i in range(0, len(df) - n + 1, n):
            window = df.iloc[i:i+n]
            has_invalid = (window[list(self.axis_cols)] == -9999).any().any()
            
            if not has_invalid:
                valid_windows += 1
                stds = window[list(self.axis_cols)].std()
                window_stds.append(stds)
                if all(stds < self.static_threshold):
                    static_windows_stds.append(stds)
                    static_windows += 1

        diagnostics = {
            'total_windows': total_windows,
            'valid_windows': valid_windows,
            'static_windows': static_windows,
            'window_stds': window_stds
        }

        if verbose:
            print(f"\nStatic Window Detection Diagnostics:")
            print(f"Total windows analyzed: {total_windows}")
            print(f"Windows without invalid values: {valid_windows}")
            print(f"Windows that passed static test: {static_windows}")
            if valid_windows > 0:
                static_stds_array = np.array(static_windows_stds)
                print(f"\nStandard deviation statistics (in g):")
                print(f"Mean std across all axes: {np.mean(static_stds_array):.4f}")
                print(f"Min std: {np.min(static_stds_array):.4f}")
                print(f"Max std: {np.max(static_stds_array):.4f}")
                print(f"Current threshold: {self.static_threshold:.4f}")
            
            if static_windows < 10:
                print("\nPossible solutions:")
                print(f"1. Try increasing window_size (currently {window_size}s)")
                print(f"2. Try increasing static_threshold (currently {self.static_threshold}g)")
                print("3. Check if your data has enough static periods")
                print("4. Verify data quality and sampling rate")

        return diagnostics
