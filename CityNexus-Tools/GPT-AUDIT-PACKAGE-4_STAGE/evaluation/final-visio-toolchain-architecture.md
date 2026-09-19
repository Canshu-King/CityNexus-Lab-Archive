# Final Visio Toolchain Architecture

CityNexus YAML Spec → Renderer Core → Visio COM/native UML.

VisioAutomation contributes typed ShapeData and connector helpers; its native UML Association routing test failed, so the next phase must use explicit native Association geometry/waypoints. MSAGL was not executed in this gate and is not adopted. `vsdx` 0.6.1 remains limited to page/shape/child-shape traversal. Raw Open XML owns SpecId, masters, Connects and ShapeSheet checks. JiaxI2 `visio-diagram` is retained as QA/routing/geometry guideline only because its diagram_* MCP interface is absent from the installed server.
