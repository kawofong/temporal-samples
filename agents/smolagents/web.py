from io import BytesIO
from time import sleep

import helium
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from smolagents import CodeAgent, LiteLLMModel, tool
from smolagents.agents import ActionStep

# Configure Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--force-device-scale-factor=1")
chrome_options.add_argument("--window-size=1000,1350")
chrome_options.add_argument("--disable-pdf-viewer")
chrome_options.add_argument("--window-position=0,0")


@tool
def search_item_ctrl_f(text: str, nth_result: int = 1) -> str:
    """
    Searches for text on the current page via Ctrl + F and jumps to the nth occurrence.
    Args:
        text: The text to search for
        nth_result: Which occurrence to jump to (default: 1)
    """
    driver = helium.get_driver()
    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
    if nth_result > len(elements):
        raise ValueError(
            f"Match nth {nth_result} not found (only {len(elements)} matches found)"
        )
    result = f"Found {len(elements)} matches for '{text}'."
    elem = elements[nth_result - 1]
    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
    result += f"Focused on element {nth_result} of {len(elements)}"
    return result


@tool
def go_back() -> None:
    """Goes back to previous page."""
    driver = helium.get_driver()
    driver.back()


@tool
def close_popups() -> str:
    """
    Closes any visible modal or pop-up on the page. Use this to dismiss pop-up windows!
    This does not work on cookie consent banners.
    """
    driver = helium.get_driver()
    webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()


# Set up screenshot callback
def save_screenshot(memory_step: ActionStep, agent: CodeAgent) -> None:
    """
    Save a screenshot of the current browser window.
    """
    sleep(1.0)  # Let JavaScript animations happen before taking the screenshot
    driver = helium.get_driver()
    current_step = memory_step.step_number
    if driver is not None:
        for (
            previous_memory_step
        ) in agent.memory.steps:  # Remove previous screenshots for lean processing
            if (
                isinstance(previous_memory_step, ActionStep)
                and previous_memory_step.step_number <= current_step - 2
            ):
                previous_memory_step.observations_images = None
        png_bytes = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(png_bytes))
        print(f"Captured a browser screenshot: {image.size} pixels")
        memory_step.observations_images = [
            image.copy()
        ]  # Create a copy to ensure it persists

    # Update observations with current URL
    url_info = f"Current url: {driver.current_url}"
    memory_step.observations = (
        url_info
        if memory_step.observations is None
        else memory_step.observations + "\n" + url_info
    )


class WebBrowserAgent:
    def __init__(self):
        self._model = LiteLLMModel(model_id="openai/gpt-4o")
        self._agent = CodeAgent(
            tools=[go_back, close_popups, search_item_ctrl_f],
            model=self._model,
            additional_authorized_imports=["helium"],
            step_callbacks=[save_screenshot],
            max_steps=20,
            verbosity_level=2,
        )
        self._agent.python_executor("from helium import *")
        self._helium_instructions = """
You can use helium to access websites. Don't bother about the helium driver, it's already managed.
We've already ran "from helium import *"
Then you can go to pages!
Code:
```py
go_to('github.com/trending')
```<end_code>

You can directly click clickable elements by inputting the text that appears on them.
Code:
```py
click("Top products")
```<end_code>

If it's a link:
Code:
```py
click(Link("Top products"))
```<end_code>

If you try to interact with an element and it's not found, you'll get a LookupError.
In general stop your action after each button click to see what happens on your screenshot.
Never try to login in a page.

To scroll up or down, use scroll_down or scroll_up with as an argument the number of pixels to scroll from.
Code:
```py
scroll_down(num_pixels=1200) # This will scroll one viewport down
```<end_code>

When you have pop-ups with a cross icon to close, don't try to click the close icon by finding its element or targeting an 'X' element (this most often fails).
Just use your built-in tool `close_popups` to close them:
Code:
```py
close_popups()
```<end_code>

You can use .exists() to check for the existence of an element. For example:
Code:
```py
if Text('Accept cookies?').exists():
    click('I accept')
```<end_code>
"""
        # Initialize the browser
        self.driver = helium.start_chrome(headless=False, options=chrome_options)

    def run(self, prompt_prefix: str) -> str:
        return self._agent.run(prompt_prefix + self._helium_instructions)


class WeatherAgent(WebBrowserAgent):
    def run(self, location: str) -> str:
        return super().run(
            f"""
I'm looking for the current temperature and weather in {location}.
Please navigate to https://www.bing.com/search?q=weather+in+{location} and give me the current temperature and weather.
"""
        )
