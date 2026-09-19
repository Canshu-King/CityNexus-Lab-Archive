# CityNexus Validator Architecture

* `vsdx` 0.6.1: page, shape, child-shape and connector traversal.
* Raw Open XML parser: `Prop.SpecId`, master references, `Connects` source/target and ShapeSheet formulas.
* Visio MCP/COM live inspection: glue, effective styles, routing and rendered geometry.

The three layers are complementary. `vsdx` 0.6.1 is not authoritative for connector endpoints, master metadata, User cells or `Prop.SpecId`; those fields must be obtained from Open XML or live COM.
