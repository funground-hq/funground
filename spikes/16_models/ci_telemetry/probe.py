"""S-231, D-124: does onnxruntime open a network connection? Run by .github/workflows/ort-telemetry.yml on Linux and macOS.

Builds a tiny model (one Add), creates a session, runs it 100 times, waits, and exits, so that create, run, idle
and interpreter exit are all covered. The workflow watches the process from outside (strace on Linux, lsof on macOS).
"""
import time

import numpy as np
import onnx
import onnxruntime as ort
from onnx import TensorProto, helper

x = helper.make_tensor_value_info("x", TensorProto.FLOAT, [1, 4])
y = helper.make_tensor_value_info("y", TensorProto.FLOAT, [1, 4])
graph = helper.make_graph([helper.make_node("Add", ["x", "x"], ["y"])], "probe", [x], [y])
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)])
model.ir_version = 9
session = ort.InferenceSession(model.SerializeToString(), providers=["CPUExecutionProvider"])
for _ in range(100):
    session.run(None, {"x": np.ones((1, 4), np.float32)})
print("onnxruntime", ort.__version__, "ran 100 times; idling 30 s")
time.sleep(30)
del session
print("done")
