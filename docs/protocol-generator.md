<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This is currently an experimental feature. To try it follow this guide.</p>
</div>

## How to run

First make sure you are inside your AEA's folder (see <a href="../quickstart">here</a> on how to create a new agent).

Then run

``` bash
aea generate protocol <path-to-protocol-specification>
```

where `<path-to-protocol-specification>` is the path to a <a href="../protocol-generator/#protocol-specification">protocol specification</a> file.

If there are no errors, this command will generate the protocol and place it in your AEA project. The name of the protocol's directory will match the protocol name given in the specification. The author will match the registered author in the CLI. The generator currently produces the following files (assuming the name of the protocol in the specification is `sample`):

* `message.py`: defines messages valid under the `sample` protocol 
* `serialisation.py`: defines how messages are serialised/deserialised 
* `__init__.py`: makes the directory a package
* `protocol.yaml`: contains package information about the `sample` protocol 
* `sample.proto` protocol buffer schema file
* `sample_pb2.py`: the generated protocol buffer implementation
* `custom_types.py`: stub implementations for custom types (created only if the specification contains custom types)

## Protocol Specification
A protocol can be described in a yaml file. As such, it needs to follow the <a href="https://pyyaml.org/wiki/PyYAMLDocumentation" target="_blank">yaml format</a>. The following is an example protocol specification:

``` yaml
---
name: two_party_negotiation
author: fetchai
version: 0.1.0
license: Apache-2.0
aea_version: '>=0.5.0, <0.6.0'
description: 'A protocol for negotiation over a fixed set of resources involving two parties.'
speech_acts:
  cfp:
    query: ct:DataModel
  propose:
    offer: ct:DataModel
    price: pt:float
  accept: {}
  decline: {}
  match_accept: {}
...
---
ct:DataModel: |
  bytes data_model = 1;
...
---
reply:
  cfp: [propose, decline]
  propose: [accept, decline]
  accept: [decline, match_accept]
  decline: []
  match_accept: []
roles: {buyer, seller}
end_states: [successful, failed]
...
```

Each protocol specification yaml file must have a minimum of one, and a maximum of three yaml documents (each yaml document is enclosed within --- and ...). 

### Basic Protocol Detail and Messages Syntax

The first yaml document is mandatory in any protocol specification. It contains some basic information about the protocol and describes the syntax of communicative messages allowed under this protocol. 

The allowed fields and what they represent are:

 * `name`: The name of the protocol (written in <a href="https://en.wikipedia.org/wiki/Snake_case" target="_blank">snake_case</a>)
 * `author`: The creator of the protocol
 * `version`: The current version of the protocol
 * `license`: Licensing information
 * `aea_version`: The version(s) of the framework that support this protocol. The format is described <a href="https://www.python.org/dev/peps/pep-0440/" target="_blank">here</a>.
 * `description`: A short description of the protocol

All of the above fields are mandatory and each is a key/value pair, where both key and value are yaml strings. 

In addition, the first yaml document in a protocol specification must describe the syntax of valid messages according to this protocol. Therefore, there is another mandatory field: `speech-acts`, which defines the set of _performatives_ valid under this protocol, and a set of _contents_ for each performative.

A _performative_ defines the type of a message (e.g. propose, accept) and has a set of _contents_ (or parameters) of varying types.

The format of the `speech-act` is as follows: `speech-act` is a dictionary, where each key is a **unique** _performative_ (yaml string), and the value is a _content_ dictionary. If a performative does not have any content, then its content dictionary is empty, e.g. `accept`, `decline` and `match_accept` in the above specification.

A content dictionary in turn is composed of key/value pairs, where each key is the name of a content (yaml string) and the value is its <a href="../protocol-generator/#types">type</a> (yaml string). For example, the `cfp` (short for 'call for proposal') performative has one content whose name is `query` and whose type is `ct:DataModel`.

#### Types

The specific types which could be assigned to contents in a protocol specification are described in the table below.

Types are either user defined (i.e. custom types) or primitive: 

* Custom types are prepended with `ct:` and their format is described using regular expression in the table below. 
* Primitive types are prepended with `pt:`. There are different categories of primitive types, e.g. `<PT>` such as integers and booleans, `<PCT>` such as sets and lists, and so on. Primitive types are compositional: 
    - For example, consider `pt:set[...]` under `<PCT>`, i.e. an unordered collection of elements without duplicates. A `pt:set[...]` describes the type of its elements (called "sub-type") in square brackets. The sub-type of a `pt:set[...]` must be a `<PT>` (e.g. `pt:int`, `pt:bool`). 
    - In describing the format of types, `/` between two sub-types should be treated as "or". For example, the sub-type of a `pt:optional[...]` is either a `<PT>`, `<CT>`, `<PCT>`, `<PMT>` or an `<MT>`.

A multi type denotes an "or" separated set of sub-types, e.g. `pt:union[pt:str, pt:int]` as the type of a `content` means `content` should either be a `pt:int` or a `pt:float`.

An optional type for a content denotes that the content's existence is optional, but if it is present, its type must match `pt:optional[...]`'s sub-type. 
                                                                                                                                                                 
| Type                       | Code          | Format                                                                                                        | Example                                  | In Python                          |
| ---------------------------| --------------| --------------------------------------------------------------------------------------------------------------|------------------------------------------|------------------------------------|
| Custom types<sup>1</sup>               | `<CT>`  | `ct:RegExp(^[A-Z][a-zA-Z0-9]*$)`                                                                              | `ct:DataModel`                           | Custom Class                       |
| Primitive types            | `<PT>`  | `pt:bytes`                                                                                                    | `pt:bytes`                               | `bytes`                            |
|                            |               | `pt:int`                                                                                                      | `pt:int`                                 | `int`                              |
|                            |               | `pt:float`                                                                                                    | `pt:float`                               | `float`                            |
|                            |               | `pt:bool`                                                                                                     | `pt:bool`                                | `bool`                             |
|                            |               | `pt:str`                                                                                                      | `pt:str`                                 | `str`                              |
| Primitive collection types | `<PCT>` | `pt:set[<PT>]`                                                                                          | `pt:set[pt:str]`                         | `FrozenSet[str]`                   |
|                            |               | `pt:list[<PT>]`                                                                                         | `pt:list[pt:int]`                        | `Tuple[int, ...]`<sup>*</sup>      |
| Primitive mapping types<sup>2</sup>    | `<PMT>` | `pt:dict[<PT>, <PT>]`                                                                 | `pt:dict[pt:str, pt:bool]`               | `Dict[str, bool]`                  |
| Multi types                | `<MT>`  | `pt:union[<PT>/<CT>/<PCT>/<PMT>, ..., <PT>/<CT>/<PCT>/<PMT>]` | `pt:union[ct:DataModel, pt:set[pt:str]]` | `Union[DataModel, FrozenSet[str]]` |
| Optional types             | `<O>`   | `pt:optional[<MT>/<PMT>/<PCT>/<PT>/<CT>]`                                       | `pt:optional[pt:bool]`                   | `Optional[bool]`                   |

*This is how variable length tuples containing elements of the same type are declared in Python*; see <a href="https://docs.python.org/3/library/typing.html#typing.Tuple" target=_blank>here</a>

### Protocol Buffer Schema

Currently, there is no official method provided by the AEA framework for describing custom types in a programming language independent format. This means that if a protocol specification includes custom types, the required implementations must be provided manually. 

Therefore, if any of the contents declared in `speech-acts` is of a custom type, the specification must then have a second yaml document, containing the protocol buffer schema code for every custom type.

You can see an example of the second yaml document in the above protocol specification.

### Dialogues

You can optionally describe some of the structural details of dialogues conforming to your protocol in a third yaml document in the protocol specification.

The allowed fields and what they represent are:

 * `reply`: The reply structure of speech-acts
 * `roles`: The roles of agents participating in dialogues
 * `end_states`: The final states a dialogue could end up in.

All of the above fields are mandatory. 

`reply` specifies for every performative, what its valid replies are. If a performative `per_1` is a valid reply to another `per_2`, this means a message with performative `per_1` can target a message whose performative is `per_2`.      

`reply` is a dictionary, where the keys are the performatives (yaml string) defined in `speech-acts`. For each performtaive key, its value is a list of performatives which are defined to be a valid reply. 
For example, valid replies to `cfp` are `propose` and `decline`.

`roles` lists the roles are agents which participate in dialogues conforming with your protocol. 
`roles` takes a set, which may contain two or one roles, each role being a yaml string. 

If there are two roles, each agent has a distinguished role in the dialogue (e.g. buyer and seller in the above specification).
If there is one role, then the two agents in a dialogue take the same role.

`end_states` lists the final states a dialogue based on your protocol may terminate in. 
`end_states` is a list of yaml strings. 

### Notes

1. Currently, there is no way to describe custom types in a programming language independent format. This means that if a protocol specification includes custom types, the required implementations must be provided manually.
    * Before generating the protocol, the protocol buffer schema code for every custom type must be provided in the protocol specification.    
    * Once the generator is called, it produces a `custom_types` module containing stub implementations for every custom type in the specification. The user must then modify this module and add implementations for every custom type in the specification. This includes implementations of how an object of a custom type can be encoded and decoded using protocol buffer.
    * Note, currently the way custom types are dealt with in the generator is admittedly inconvenient. The reason is, the generator does not know the structure of custom types and how they may be serialised/deserialised. Although this approach works, it is only a temporary solution until further work on a programming language-independent type description language is finished (similar to how the generator is designed to be a programming language-independent protocol description language).
2. Currently, the first element in `pt:dict` cannot be a `<CT>`, `pt:float` or  `pt:bytes`. This is because of a constraint in protocol buffer version 3 which is the framework's underlying serialisation mechanism. In a future version, we may address this limitation, in which case we will relax this constraint.
3. In protocol buffer version 3, which is the version used by the generator, there is no way to check whether an optional field (i.e. contents of type `pt:optional[...]`) has been set or not (see discussion <a href="https://github.com/protocolbuffers/protobuf/issues/1606" target=_blank>here</a>). In proto3, all optional fields are assigned a default value (e.g. `0` for integers types, `false` for boolean types, etc). Therefore, given an optional field whose value is the default value, there is no way to know from the optional field itself, whether it is not set, or in fact is set but its value happens to be the default value. Because of this, in the generated protocol schema file (the `.proto` file), for every optional content there is a second field that declares whether this field is set or not. We will maintain this temporary solution until a cleaner alternative is found.
4. Be aware that currently, using the generated protocols in python, there might be some rounding errors when serialising and then deserialising values of `pt:float` contents.


## Demo instructions

First, create a new AEA project:

``` bash
aea create my_aea
cd my_aea
```

Second, run the generator on the sample specification:

``` bash
aea generate protocol ../examples/protocol_specification_ex/sample.yaml
```

This will generate the protocol and place it in your AEA project.

Third, try generating other protocols by first defining a specification, then running the generator.


<br />
