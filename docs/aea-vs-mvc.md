The AEA framework borrows several concepts from popular web frameworks like <a href="https://www.djangoproject.com/" target="_blank">Django</a> and <a href="https://rubyonrails.org/" target="_blank">Ruby on Rails</a>.

## MVC

Both aforementioned web frameworks use the <a href="https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller" target="_blank">MVC</a> (model-view-controller) architecture.

- Models: contain business logic and data representations
- View: contain the HTML templates
- Controller: deals with the request-response handling

## Comparison to AEA framework

The AEA framework is based on <a href="https://en.wikipedia.org/wiki/Asynchronous_communication" target="_blank">asynchronous messaging</a> and other <a href="../agent-oriented-development" target="_blank">agent-oriented development assumptions</a>. Hence, there is not a direct one-to-one relationship between MVC based architectures and the AEA framework. Nevertheless, there are some parallels which can help a developer familiar with MVC make quick progress in the AEA framework, in particular the development of `Skills`:

- <a href="../api/skills/base#handler-objects">`Handler`</a>: receives messages for the protocol it is registered against and is supposed to handle these messages. Handlers are the reactive parts of a skill and can be thought of as similar to the `Controller` in MVC. They can also send new messages.
- <a href="../api/skills/base#behaviour-objects">`Behaviour`</a>: a behaviour encapsulates proactive components of the agent. Since web apps do not have any goals or intentions, they do not proactively pursue an objective. Therefore, there is no equivalent concept in MVC. Behaviours also can, but do not have to, send messages.
- <a href="../api/skills/tasks#task-objects">`Task`</a>: they are meant to deal with long-running executions and can be thought of as the equivalent of background tasks in traditional web apps.
- <a href="../api/skills/base#model-objects">`Model`</a>: they implement business logic and data representation, and as such, they are similar to the `Model` in MVC.

<img src="../assets/skill-components.jpg" alt="AEA Skill Components" class="center" style="display: block; margin-left: auto; margin-right: auto;width:80%;">

The `View` concept is probably best compared to the `Message` of a given `Protocol` in the AEA framework. Whilst views represent information to the client, messages represent information sent to other agents, other agent components and services.

## Next steps

We recommend you continue with the next step in the 'Getting Started' series:

- <a href="../skill-guide">Build a skill for an AEA</a>

<br />
