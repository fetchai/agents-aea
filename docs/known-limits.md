The AEA framework makes a multitude of tradeoffs.

Here we present an incomplete list of known limitations:

- The <a href="../api/aea_builder#aeabuilder-objects">`AEABuilder`</a> checks the consistency of packages at the `add` stage. However, it does not currently check the consistency again at the `load` stage. This means, if a package is tampered with after it is added to the `AEABuilder` then these inconsistencies might not be detected by the `AEABuilder`.

- The <a href="../api/aea_builder#aeabuilder-objects">`AEABuilder`</a> assumes that packages with public ids of identical author and package name have a matching version. As a result, if a developer uses a package with matching author and package name but different version in the public id, then the `AEABuilder` will not detect this and simply use the last loaded package.

- The order in which `setup` and `teardown` are called on the skills, and `act` is called on the behaviours, is not guaranteed. Skills should be designed to work independently. Where skills use the `shared_context` to exchange information they must do so safely.

<br />
