<a id="aea.helpers.dependency_tree"></a>

# aea.helpers.dependency`_`tree

This module contains the code to generate dependency trees from registries.

<a id="aea.helpers.dependency_tree.load_yaml"></a>

#### load`_`yaml

```python
def load_yaml(file_path: Path) -> Tuple[Dict, List[Dict]]
```

Load yaml file.

<a id="aea.helpers.dependency_tree.dump_yaml"></a>

#### dump`_`yaml

```python
def dump_yaml(file_path: Path,
              data: Dict,
              extra_data: Optional[List[Dict]] = None) -> None
```

Dump yaml file.

<a id="aea.helpers.dependency_tree.to_plural"></a>

#### to`_`plural

```python
def to_plural(string: str) -> str
```

Convert component to plural

<a id="aea.helpers.dependency_tree.reduce_sets"></a>

#### reduce`_`sets

```python
def reduce_sets(list_of_sets: List[Set]) -> Set[PackageId]
```

Reduce a list of sets to one dimentional set.

<a id="aea.helpers.dependency_tree.to_package_id"></a>

#### to`_`package`_`id

```python
def to_package_id(public_id: str, package_type: str) -> PackageId
```

Convert to public id.

<a id="aea.helpers.dependency_tree.DependencyTree"></a>

## DependencyTree Objects

```python
class DependencyTree()
```

This class represents the dependency tree for a registry.

<a id="aea.helpers.dependency_tree.DependencyTree.get_all_dependencies"></a>

#### get`_`all`_`dependencies

```python
@staticmethod
def get_all_dependencies(item_config: Dict) -> List[PackageId]
```

Returns a list of all available dependencies.

<a id="aea.helpers.dependency_tree.DependencyTree.resolve_tree"></a>

#### resolve`_`tree

```python
@classmethod
def resolve_tree(cls, dependency_list: Dict[PackageId,
                                            List[PackageId]]) -> Dict
```

Resolve dependency tree.

**Arguments**:

- `dependency_list`: the adjacency list of the dependency graph

**Returns**:

the dependency tree

<a id="aea.helpers.dependency_tree.DependencyTree.flatten_tree"></a>

#### flatten`_`tree

```python
@classmethod
def flatten_tree(cls, dependency_tree: Dict, flat_tree: List[List[PackageId]],
                 level: int) -> None
```

Flatten tree.

<a id="aea.helpers.dependency_tree.DependencyTree.find_packages_in_a_project"></a>

#### find`_`packages`_`in`_`a`_`project

```python
@staticmethod
def find_packages_in_a_project(project_dir: Path) -> List[Tuple[str, Path]]
```

Find packages in an AEA project.

<a id="aea.helpers.dependency_tree.DependencyTree.find_packages_in_a_local_repository"></a>

#### find`_`packages`_`in`_`a`_`local`_`repository

```python
@staticmethod
def find_packages_in_a_local_repository(
        packages_dir: Path) -> List[Tuple[str, Path]]
```

Find packages in a local repository.

<a id="aea.helpers.dependency_tree.DependencyTree.generate"></a>

#### generate

```python
@classmethod
def generate(cls,
             packages_dir: Path,
             from_project: bool = False) -> List[List[PackageId]]
```

Returns PublicId to hash mapping.

