import argparse
import os
import io
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification


# ─── INFERENCE FUNCTIONS (required for deployment) ───

def model_fn(model_dir):
    """Load model from the model_dir"""
    model = joblib.load(os.path.join(model_dir, 'model.joblib'))
    return model


def input_fn(request_body, content_type='text/csv'):
    """Parse input data"""
    if content_type == 'text/csv':
        df = pd.read_csv(io.StringIO(request_body), header=None)
        return df
    raise ValueError(f"Unsupported content type: {content_type}")


def predict_fn(input_data, model):
    """Make predictions"""
    return model.predict(input_data)


def output_fn(prediction, accept='text/csv'):
    """Format prediction output"""
    if accept == 'text/csv':
        return ','.join(str(p) for p in prediction), 'text/csv'
    raise ValueError(f"Unsupported accept type: {accept}")


# ─── TRAINING ───

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--output-data-dir', type=str,
                        default=os.environ.get('SM_OUTPUT_DATA_DIR', '/tmp'))

    parser.add_argument('--model-dir', type=str,
                        default=os.environ.get('SM_MODEL_DIR', '/tmp'))

    args = parser.parse_args()

    # Generate fake training data
    X, y = make_classification(
        n_samples=1000,
        n_features=10,
        random_state=42
    )

    # Convert to dataframe
    df = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])

    # Save baseline data (important for drift detection later)
    os.makedirs('/opt/ml/input/data/train', exist_ok=True)
    df.to_csv('/opt/ml/input/data/train/baseline.csv', index=False)

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Save model
    os.makedirs(args.model_dir, exist_ok=True)
    joblib.dump(model, os.path.join(args.model_dir, 'model.joblib'))

    print("✅ Training complete!")