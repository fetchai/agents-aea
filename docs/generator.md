<div class="admonition note">
  <p class="admonition-title">Note</p>
  <p>This is currently an experimental feature. To try it follow this guide.</p>
</div>

## Preparation instructions

### Dependencies

Follow the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start.

### How to run

First make sure you are inside your AEA's folder (see <a href="../quickstart">here</a> on how to create a new agent).

Then run  

``` bash
aea generate protocol <path-to-protocol-specification>
```

where `<path-to-protocol-specification>` is the relative path to a <a href="../generator/#protocol-specification">protocol specification</a>  file. 


If there are no errors, this command will generate the protocol and place it in your AEA project. The name of the protocol's directory will match the protocol name given in the specification.

## Protocol Specification
A protocol can be described in a yaml file.
As such, it needs to follow the <a href="https://pyyaml.org/wiki/PyYAMLDocumentation" target="_blank">yaml format</a>. 
The following is an example protocol specification:

```yaml
name: two_party_negotiation
author: fetchai
version: 0.1.0
license: Apache 2.0
description: 'A protocol for negotiation over a fixed set of resources involving two parties.'
speech_acts:
  cfp:
    query: ct:DataModel
  propose:
    query: ct:DataModel
    price: pt:float
  accept: {}
  decline: {}
  match_accept: {}
```


Each protocol specification yaml file contains some basic information about the protocol. The allowed fields and what they represent are:

 * `name`: The name of the protocol (written in <a href="https://en.wikipedia.org/wiki/Snake_case" target="_blank">snake_case</a>)
 * `authors`: List of authors
 * `version`: The current version of the protocol
 * `license`: Licensing information
 * `description`: A short description of the protocol

Each field is a key/value pair, where both the key and the value are yaml strings. Every field is mandatory. 

Furthermore, the protocol specification must describe the syntax of valid messages according to this protocol.
Therefore, there is another mandatory field: `speech-acts`, which defines the set of performatives valid under this protocol, and a set of contents (i.e. parameters) for each performative.  

The format of the `speech-act` is as follows:
`speech-act` is a dictionary, where each key is a unique **performative** (yaml string), and the value is a **content** dictionary. If a performative `perm` does not have any content, then its content dictionary is empty, e.g. simply denoted as `perm: {}`.

Each content dictionary is composed of key/value pairs, where each key is the name of a content (yaml string) and the value is its <a href="../generator/#types">type</a> (yaml string).  

### Types

The specific types which could be assigned to contents in a protocol specification are described in the table below.

Types are either user defined (i.e. custom type) or primitive. 

Custom types are prepended with "ct:" and their format is described using regular expression in the table below. 

Primitive types are prepended with "pt:". 

There are different categories of primitive types, e.g. &lt;PT&gt; such as int and bool, &lt;PCT&gt; such as sets and lists, and so on. 

Primitive types have a compositional format. For example, consider sets under &lt;PCT&gt;, i.e. unordered, immutable collections with no duplicate elements. Sets must describe the type of their elements in square brackets and these could either be &lt;PT&gt; (e.g. `pt:int`, `pt:bool`) or &lt;CT&gt; (i.e. a custom type). Therefore, when describing the format of types in the table below, `/` between two type categories `T1` and `T2` means "or", i.e. "either a `T1` or a `T2` type".

Multi types are an "or" separated set of sub-types. A multi type `pt:int or pt:float` means the type is either `pt:int` or `pt:float`.

An optional type for a content indicates that the content is optional, but if it is present, its type must match what is described in the square brackets. 

<table>
<tr>
<td valign="top">
<strong>Type</strong>
</td>
<td valign="top">
<strong>Code</strong>
</td>
<td valign="top">
<strong>Format</strong>
</td>
<td valign="top">
<strong>Example</strong>
</td>
<td valign="top">
<strong>In Python</strong>
</td>
</tr>
<tr>
<td valign="top">
<strong>Custom types</strong>
</td>
<td valign="top">
&lt;CT&gt;
</td>
<td valign="top">
ct:RegExp(^[A-Z][a-zA-Z0-9_]*[a-zA-Z0-9]$)
</td>
<td valign="top">
ct:DataModel
</td>
<td valign="top">
Custom Class
</td>
</tr>
<tr>
<td rowspan="5" valign="top">
<strong>Primitive types</strong>
</td>
<td rowspan="5" valign="top">
&lt;PT&gt;
</td>
<td valign="top">
pt:byte
</td>
<td valign="top">
pt:byte
</td>
<td valign="top">
bytes
</td>
</tr>
<tr>
<td valign="top">
pt:int
</td>
<td valign="top">
pt:int
</td>
<td valign="top">
int
</td>
</tr>
<tr>
<td valign="top">
pt:float
</td>
<td valign="top">
pt:float
</td>
<td valign="top">
float
</td>
</tr>
<tr>
<td valign="top">
pt:bool
</td>
<td valign="top">
pt:bool
</td>
<td valign="top">
bool
</td>
</tr>
<tr>
<td valign="top">
pt:str
</td>
<td valign="top">
pt:str
</td>
<td valign="top">
str
</td>
</tr>
<tr>
<td rowspan="2" valign="top">
<strong>Primitive collection types</strong>
</td>
<td rowspan="2" valign="top">
&lt;PCT&gt;
</td>
<td valign="top">
pt:set[&lt;PT&gt;/&lt;CT&gt;]
</td>
<td valign="top">
pt:set[pt:int]
</td>
<td valign="top">
FrozenSet
</td>
</tr>
<tr>
<td valign="top">
pt:list[&lt;PT&gt;/&lt;CT&gt;]
</td>
<td valign="top">
pt:list[ct:DataModel]
</td>
<td valign="top">
Tuple
</td>
</tr>
<tr>
<td valign="top">
<strong>Primitive mapping types</strong>
</td>
<td valign="top">
&lt;PMT&gt;
</td>
<td valign="top">
pt:dict[&lt;PT&gt;/&lt;CT&gt;,&nbsp; &lt;PT&gt;/&lt;CT&gt;]
</td>
<td valign="top">
pt:dict[pt:str, ct:Error]
</td>
<td valign="top">
Dict
</td>
</tr>
<tr>
<td valign="top">
<strong>Multi types</strong>
</td>
<td valign="top">
&lt;MT&gt;
</td>
<td valign="top">
&lt;PT&gt;/&lt;CT&gt;/&lt;PCT&gt;/&lt;PMT&gt; or ... or &lt;PT&gt;/&lt;CT&gt;/&lt;PCT&gt;/&lt;PMT&gt;
</td>
<td valign="top">
pt:str or pt:list[p:bool]
</td>
<td valign="top">
Union
</td>
</tr>
<tr>
<td valign="top">
<strong>Optional types</strong>
</td>
<td valign="top">
&lt;O&gt;
</td>
<td valign="top">
pt:optional[&lt;MT&gt;/&lt;PMT&gt;/&lt;PCT&gt;/&lt;PT&gt;/&lt;CT&gt;]
</td>
<td valign="top">
pt:optional[pt:list[pt:int]]
</td>
<td valign="top">
Optional
</td>
</tr>
</table>


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