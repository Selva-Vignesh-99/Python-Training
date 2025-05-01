import os
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QLabel, QPushButton,QHBoxLayout, QVBoxLayout, QListWidget, QComboBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageFilter, ImageEnhance

class ImageEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ImageEditor")
        self.resize(900, 700)
        self.image = None
        self.original = None
        self.filename = None
        self.save_folder = "edits/"

        self.btn_folder = QPushButton("folder")
        self.file_list = QListWidget()
        self.btn_left = QPushButton("Left")
        self.btn_right = QPushButton("Right")
        self.btn_mirror = QPushButton("Mirror")
        self.btn_sharpness = QPushButton("Sharpen")
        self.btn_gray = QPushButton("B/W")
        self.btn_saturation = QPushButton("Color")
        self.btn_contrast = QPushButton("Contrast")
        self.btn_blur = QPushButton("Blur")
        # DropDown Box
        self.filter_box = QComboBox()
        self.filter_box.addItem("Original")
        self.filter_box.addItem("Left")
        self.filter_box.addItem("Right")
        self.filter_box.addItem("Sharpen")
        self.filter_box.addItem("B/W")
        self.filter_box.addItem("Color")
        self.filter_box.addItem("Contrast")
        self.filter_box.addItem("Blur")
        self.filter_box.currentTextChanged.connect(self.handle_filter)

        self.picture_box = QLabel("Image will appear here")

        # App Design
        self.master_layout = QHBoxLayout()
        
        self.col1 = QVBoxLayout()
        self.col2 = QVBoxLayout()

        self.col1.addWidget(self.btn_folder)
        self.col1.addWidget(self.file_list)
        self.col1.addWidget(self.filter_box)
        self.col1.addWidget(self.btn_left)
        self.col1.addWidget(self.btn_right)
        self.col1.addWidget(self.btn_mirror)
        self.col1.addWidget(self.btn_sharpness)
        self.col1.addWidget(self.btn_gray)
        self.col1.addWidget(self.btn_saturation)
        self.col1.addWidget(self.btn_contrast)
        self.col1.addWidget(self.btn_blur)

        self.col2.addWidget(self.picture_box)

        self.master_layout.addLayout(self.col1, 20)
        self.master_layout.addLayout(self.col2, 80)

        self.setLayout(self.master_layout)
        self.btn_folder.clicked.connect(self.getWorkDirectory)
        self.file_list.clicked.connect(self.displayImage)
        self.btn_gray.clicked.connect(lambda: self.transform_image("B/W"))
        self.btn_left.clicked.connect(lambda: self.transform_image("Left"))
        self.btn_right.clicked.connect(lambda: self.transform_image("Right"))
        self.btn_mirror.clicked.connect(lambda: self.transform_image("Mirror"))
        self.btn_sharpness.clicked.connect(lambda: self.transform_image("Sharpen"))
        self.btn_saturation.clicked.connect(lambda: self.transform_image("Color"))
        self.btn_contrast.clicked.connect(lambda: self.transform_image("Contrast"))
        self.btn_blur.clicked.connect(lambda: self.transform_image("Blur"))
        self.working_directory = ""

        

    def filter(self, files, extensions):
        results = []
        for file in files:
            for ext in extensions:
                if file.endswith(ext):
                    results.append(file)
        return results
    
    def getWorkDirectory(self):
        self.working_directory = QFileDialog.getExistingDirectory()
        extensions = ['.jpg', '.jpeg', '.png', '.svg']
        filenames = self.filter(os.listdir(self.working_directory), extensions)
        self.file_list.clear()
        for filename in filenames:
            self.file_list.addItem(filename)

    def load_image(self, filename):
        self.filename = filename
        fullname = os.path.join(self.working_directory, self.filename)
        self.image = Image.open(fullname)
        self.original = self.image.copy()

    def save_image(self):
        path = os.path.join(self.working_directory, self.save_folder)
        if not(os.path.exists(path) or os.path.isdir(path)):
            os.mkdir(path)
        fullname = os.path.join(path, self.filename)
        self.image.save(fullname)

    def show_image(self, path):
        self.picture_box.hide()
        image = QPixmap(path)
        w, h = self.picture_box.width(), self.picture_box.height()
        image = image.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio)
        self.picture_box.setPixmap(image)
        self.picture_box.show()

    def displayImage(self):
        if self.file_list.currentRow() >= 0:
            filename = self.file_list.currentItem().text()
            self.load_image(filename)
            self.show_image(os.path.join(self.working_directory, self.filename))

    def transform_image(self, filter_name):
        transformations = {
            "Left": lambda image: image.transpose(Image.Transpose.ROTATE_90),
            "Right": lambda image: image.transpose(Image.Transpose.ROTATE_270),
            "Sharpen": lambda image: image.filter(ImageFilter.SHARPEN),
            "B/W": lambda image: image.convert("L"),
            "Color": lambda image: ImageEnhance.Color(image).enhance(1.5),
            "Color": lambda image: ImageEnhance.Contrast(image).enhance(1.5),
            "Blur": lambda image: image.filter(ImageFilter.BLUR),
            "Mirror": lambda image: image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        }
        transform_function = transformations.get(filter_name)
        if transform_function:
            self.image = transform_function(self.image)
        self.save_image()
        image_path = os.path.join(self.working_directory, self.save_folder, self.filename)
        self.show_image(image_path)

    def apply_filter(self, filter_name):
        mapping = {
            "Left": lambda image: image.transpose(Image.Transpose.ROTATE_90),
            "Right": lambda image: image.transpose(Image.Transpose.ROTATE_270),
            "Sharpen": lambda image: image.filter(ImageFilter.SHARPEN),
            "B/W": lambda image: image.convert("L"),
            "Color": lambda image: ImageEnhance.Color(image).enhance(1.5),
            "Color": lambda image: ImageEnhance.Contrast(image).enhance(1.5),
            "Blur": lambda image: image.filter(ImageFilter.BLUR),
            "Mirror": lambda image: image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        }
        if filter_name == 'Original':
            self.image = self.original.copy()
        else:
            filter_function = mapping.get(filter_name)
            if filter_function:
                self.image = filter_function(self.image)
                self.save_image()
                image_path = os.path.join(self.working_directory, self.save_folder, self.filename)
                self.show_image(image_path)
            pass
        self.save_image()
        image_path = os.path.join(self.working_directory, self.save_folder, self.filename)
        self.show_image(image_path)

    def handle_filter(self):
        if self.file_list.currentRow() >= 0:
            select_filter = self.filter_box.currentText()
            self.apply_filter(select_filter)

if __name__ in "__main__":
    app = QApplication([])
    main_window = ImageEditor()
    main_window.show()
    app.exec()