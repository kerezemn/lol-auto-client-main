import pyautogui
import time

class Detector:
    def __init__(self, image_path : str, delay_seconds : float, confidence : float, click = False, trigger_func = None, get_searching = None, search_name = "", alternative_paths = []) -> None:
        self.image_path = image_path
        self.confidence = confidence
        self.click = click
        self.trigger_func = trigger_func
        self.get_searching = get_searching
        self.search_name = search_name

        self.delay_seconds = delay_seconds
        self.last_frame_time = time.time()

        self.images = alternative_paths.copy()
        self.images.insert(0, self.image_path)

        self.img_pos = None
    
    def check_images(self) -> None:
        for img in self.images:
            if self.confidence:
                self.img_pos = pyautogui.locateCenterOnScreen(img, confidence = self.confidence)

            else:
                self.img_pos = pyautogui.locateCenterOnScreen(img)

            if self.img_pos:
                break
    
    def change_image(self, img_index : int, img_path : str) -> None:
        self.images[img_index] = img_path
    
    def update(self) -> None:
        # Delay ve Queue check
        if (time.time() - self.last_frame_time < self.delay_seconds):
            return

        if self.get_searching and (self.get_searching() != self.search_name):
            return
        
        self.check_images()
        
        if self.img_pos:
            if self.click:
                pyautogui.moveTo(self.img_pos)
                pyautogui.click()

            if self.trigger_func:
                self.trigger_func()
    
        self.last_frame_time = time.time()