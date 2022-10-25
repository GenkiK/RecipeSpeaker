from pathlib import Path

import cv2
import numpy as np
import pyocr
from PIL import Image


def bgr2rgb(img_bgr):
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)


def binarize(img_rgb, th=255 // 2):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(img_gray, th, 255, cv2.THRESH_BINARY)
    return img_bin


def binarize_otsu(img_rgb):
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, img_bin = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return img_bin


def erode(img_bin, kernel_size=5, iterations=1):
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    return cv2.erode(img_bin, kernel, iterations)


def find_contours(img):
    contours, _ = cv2.findContours(img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    return contours


class OCR:
    def __init__(self, imgpath=Path("./recipes/recipe6.png")) -> None:
        self.imgpath = imgpath
        self.procedure_imgs = []
        self.read_img()
        self.preprocess()

    def read_img(self):
        img_bgr = cv2.imread(str(self.imgpath))
        self.img = bgr2rgb(img_bgr)
        self.img_h, self.img_w, _ = self.img.shape
        self.img_bin = binarize_otsu(self.img)

    def preprocess(self):
        contours = find_contours(self.img_bin)
        # 画像全面を覆うほど大きくなく，ある程度の大きさを持つ矩形は，画像中の写真であるとして白塗りする
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if (w < self.img_w * 0.9 and h < self.img_h * 0.9) and (w > self.img_w * 0.05 or h > self.img_h * 0.05):
                self.img_bin[y : y + h, x : x + w] = 255
        eroded_img = erode(self.img_bin, 26, 1)
        contours = find_contours(eroded_img)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > self.img_w * 0.03 and h > self.img_h * 0.03 and h * w < self.img_w * self.img_h * 0.1:
                self.procedure_imgs.append(self.img[y : y + h, x : x + w, :])

    def detect_chars(self):
        tool = pyocr.get_available_tools()[0]
        builder = pyocr.builders.TextBuilder(tesseract_layout=6)

        procedures = {}
        for procedure_img in self.procedure_imgs:
            procedure_bin = binarize(procedure_img, th=180)
            # procedure_bin = binarize_otsu(procedure_img)

            # 上半分・下半分・左半分・右半分で黒いピクセルが80%以上を占めるとき，それは主に画像である不要な領域なので排除する
            # is_image_box = False
            # h, w, _ = procedure_img.shape
            # for left, right, up, bottom in [[0, w, 0, h // 2], [0, w, h // 2, h], [0, w // 2, 0, h], [w // 2, w, 0, h]]:
            #     if cv2.countNonZero(procedure_bin[up:bottom, left:right]) < h * w * 0.2:
            #         is_image_box = True

            # dp:float  投票器の解像度．大きいほど検出基準が緩くなる
            # minDist:float  検出される円同士が最低限離れている距離
            # param1:float  内部で行われているCanny法によるエッジ検出の上限値
            # param2:float  円の中心を検出する際の閾値．低い値にすると誤検出が多くなる
            # circles = cv2.HoughCircles(procedure_bin, cv2.HOUGH_GRADIENT, dp=0.1, minDist=100, param1=100, param2=30, minRadius=20, maxRadius=50)
            circles = cv2.HoughCircles(
                procedure_bin,
                cv2.HOUGH_GRADIENT,
                dp=0.1,
                minDist=min(self.img_h, self.img_w) // 20,
                param1=100,
                param2=30,
                minRadius=min(self.img_h, self.img_w) // 100,
                maxRadius=min(self.img_h, self.img_w) // 50,
            )
            if circles is not None:
                for circle in circles[0]:
                    procedure_bin = cv2.circle(
                        procedure_bin, (int(circle[0]), int(circle[1])), int(circle[2]), 255, min(self.img_h, self.img_w) // 150
                    )

            text = tool.image_to_string(Image.fromarray(procedure_bin), lang="jpn", builder=builder)
            text = text.replace("\n", "").replace(" ", "")

            nums = [str(i) for i in range(10)]
            if len(text) > 5:
                if text[0] in nums:
                    procedures[int(text[0])] = text[0] + "番．．．" + text[1:]
                elif text[1] in nums:
                    # 先頭の一文字目に余計なものが入っている場合のみ許容する
                    # HACK: 正規表現を用いて実装可能
                    procedures[int(text[1])] = text[1] + "番．．．" + text[2:]
        max_key = max(procedures)
        procedures[max_key] += "．．これでレシピは以上です．"
        return procedures
