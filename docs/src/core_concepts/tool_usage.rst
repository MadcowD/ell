=========== 
Tool Usage
===========

Tools in ell allow language models to interact with external functions or APIs.

.. code-block:: python

   @ell.tool()
   def get_weather(location: str):
       # Implementation to fetch weather data
       pass

   @ell.complex(model="gpt-4", tools=[get_weather])
   def weather_assistant(query: str):
       return [
           ell.system("You can use the get_weather tool to fetch weather information."),
           ell.user(query)
       ]