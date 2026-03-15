# 🛡️ Sentinel-AI: Enterprise Hybrid Intrusion Detection System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=tensorflow)
![XGBoost](https://img.shields.io/badge/XGBoost-179C52?style=for-the-badge&logo=xgboost)

Sentinel-AI is a next-generation network security platform that combines traditional signature-based detection with deep learning anomaly detection. Built for enterprise-grade deployment, it intercepts network traffic, analyzes it in real-time, and provides interactive telemetry, Explainable AI (XAI) diagnostics, and global threat mapping.

## 🧠 Hybrid Architecture

This system utilizes a dual-engine machine learning pipeline to maximize detection rates while minimizing false positives, achieving a **91.47% accuracy** on the rigorous KDDTest+ network dataset.

1. **XGBoost Classifier (Signature Detection):** Trained to instantly recognize the static signatures of known network attacks.
2. **Deep Autoencoder (Zero-Day Anomaly Detection):** A neural network trained exclusively on benign traffic. It calculates a dynamic Mean Squared Error (MSE) reconstruction score to flag previously unseen, zero-day anomalies that bypass traditional firewalls.

## ✨ Key Features

* **Live Network Telemetry:** Real-time visualization of dynamic Z-score thresholds and autoencoder MSE deviations.
* **Explainable AI (XAI):** Automatically isolates and displays the top mathematical feature deviations causing a packet to be flagged.
* **Global Threat Intelligence (OSINT):** Integrates with the AbuseIPDB API to verify attacking IPs and extract geographical origins.
* **Threat Origin Map:** Maps the live geolocation of intercepted attacks on an interactive global dashboard.
* **Automated Alerting:** Fires real-time critical alerts containing attack diagnostics to a dedicated Discord security channel.
* **Auto-Pilot Sequencer:** A built-in simulation engine that sequentially processes live traffic samples for presentation and testing purposes.

## 📂 Repository Structure

* `src/app.py`: The core Streamlit enterprise dashboard and inference engine.
* `newnb.ipynb`: The Jupyter Notebook containing the data preprocessing, Autoencoder design, and XGBoost training pipeline.
* `deep_autoencoder.h5`: The compiled TensorFlow/Keras neural network for anomaly detection.
* `hybrid_xgb_model.json`: The trained XGBoost model for signature detection.
* `deployment_config.json`: Stores calculated deployment baselines and dynamic anomaly thresholds.
* `kdd_feature_names.csv`: The extracted network features used for XAI mapping.
* `sample_traffic.csv` & `sample_labels.csv`: Simulated deployment data for the live Auto-Pilot dashboard.
* `requirements.txt`: Python package dependencies.

## 🚀 How to Run Locally

1. **Clone the repository:**
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   cd YOUR_REPO_NAME

2. **Create a virtual environment and activate it:**
   python3 -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate

3. **Install the required dependencies:**
   pip install -r requirements.txt

4. **Boot the platform:**
   streamlit run src/app.py

## 🛠️ Tech Stack

* **Machine Learning:** TensorFlow/Keras, XGBoost, Scikit-Learn
* **Data Processing:** Pandas, NumPy
* **Frontend/UI:** Streamlit, Plotly
* **APIs:** AbuseIPDB, Discord Webhooks