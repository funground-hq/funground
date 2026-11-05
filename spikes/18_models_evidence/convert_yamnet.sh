#!/bin/sh
# Spike 18: convert Google's YAMNet SavedModel (TF Hub google/yamnet/1) to ONNX with tf2onnx. Usage: convert_yamnet.sh VENV SAVED_MODEL_DIR OUT.onnx
# Pinned (Python 3.11.x, Linux x86-64): tensorflow-cpu==2.15.1 tf2onnx==1.16.1 onnx==1.17.0 numpy<2 (resolved 1.26.4); opset 13.
set -e
CUDA_VISIBLE_DEVICES= TF_CPP_MIN_LOG_LEVEL=2 "$1/bin/python" -I -m tf2onnx.convert --saved-model "$2" --signature_def serving_default --opset 13 --output "$3"
