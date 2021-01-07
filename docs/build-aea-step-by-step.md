
Building an AEA step by step (ensure you have followed the <a href="../quickstart/#preliminaries">Preliminaries</a> and <a href="../quickstart/#installation">Installation</a> sections from the AEA quick start first):
<ol>
<li>Set up your AEA project with the CLI: `aea create my_aea && cd my_aea` </li>
<li>Look at, then add the right <a href="../connection/">connections</a> for your use case:
	`aea search connections`, then `aea add connection [public_id]`
</li>
<li>Look for, then add or generate the <a href="../protocol/">protocols</a> you require: `aea search protocols`, then `aea add protocol [public_id]` or `aea generate protocol [path_to_specification]`</li>
<li>Look for, then add or code the <a href="../skill/">skills</a> you need: `aea search skills`, then `aea add skill [public_id]`. <a href="../skill-guide/">This guide</a> shows you step by step how to develop a skill.</li>
<li>Where required, scaffold any of the above resources with the <a href="../scaffolding/">scaffolding tool</a> or generate a protocol with the <a href="../protocol-generator/">protocol generator</a>.</li>
<li>Now, run your AEA: `aea run --connections [public_id]`</li> 
</ol>

See information on the CLI tool <a href="../cli-how-to/" target="_blank">here</a> for all the available commands.</li>
