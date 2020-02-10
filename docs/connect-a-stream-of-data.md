The AEA framework enables us to extend the agent by creating different models based on usage. To connect a 
life-stream of data (for example a sensor) you will need to implement your logic for communication with the source.

### Option 1:

You can create a wrapper class that communicates with the source and import this class in your strategy class that inherits from the Model abstract class. 

### Option 2:

You can use a third-party library by listing the dependency in the skill's `.yaml` file. Then you can import this library in a strategy class that inherits
from the Model abstract class. 
You can find example of this implementation in the <a href='/thermometer-skills-step-by-step/#step4-create-the-strategy_1'> thermometer step by step guide </a>
