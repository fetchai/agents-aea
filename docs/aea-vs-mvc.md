The AEA borrows several concepts from popular web frameworks like Django and Ruby on Rails.

Both aforementioned web frameworks use the popular MVC (model-view-controller) architecture.

- Models: contain business logic and data representations
- View: contain the html templates
- Controller: deals with the request-response handling

The AEA framework is based on asynchroneous messaging. Hence there is not a direct 1-1 relationship between MVC based architectures and the AEA framework. Nevertheless, there are some parallels which can help a developer familiar with MVC make progress in the AEA framework, in particular the development of Skills, quickly:

- `Handler`: receive the messages for the protocol they are registered against and are supposed to handle these messages. They are the reactive parts of a skill and can be thought of as similar to the `Controller`.
- `Behaviour`: a behaviour encapsulates pro-active components of the agent. Since web apps do not have any goals or intentions they do not pro-actively pursue an objective. Therefore there is no equivalent concept in MVC.
- `Task`: they are meant to deal with long running executions and can be thought of as the equivalent of background tasks in traditional web apps.
- `SharedClass`: they implement business logic and data representation, as such they are similar to `Models` in MVC.

<br />
