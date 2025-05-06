import cv2
import numpy as np
import telebot
import os
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# توکن ربات (جایگزین کنید)
TOKEN = '8087872727:AAG6_Fy_SL6z-s_cJkojfihiBUVd-UfvSRM'
bot = telebot.TeleBot(TOKEN)

def detect_bowls(frame):
    """تشخیص کاسه‌های نارنجی"""
    try:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # محدوده رنگ نارنجی در HSV
        lower_orange = np.array([10, 100, 100])
        upper_orange = np.array([25, 255, 255])
        mask = cv2.inRange(hsv, lower_orange, upper_orange)

        # حذف نویز
        kernel = np.ones((7,7), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bowls = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 500 < area < 20000:
                bowls.append(cnt)

        return bowls

    except Exception as e:
        logger.error(f"خطا در تشخیص کاسه‌ها: {e}")
        return []

def process_video(video_path):
    """پردازش ویدیو با قابلیت ردیابی"""
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("خطا در باز کردن ویدیو")
            
        # دریافت مشخصات ویدیو
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # آماده‌سازی ویدیوی خروجی
        output_path = 'output.mp4'
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # رنگ‌های متمایز برای کاسه‌ها
        colors = [
            (255, 50, 50),   # آبی
            (50, 255, 50),   # سبز
            (50, 50, 255)    # قرمز
        ]
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # تشخیص کاسه‌ها
            bowls = detect_bowls(frame)
            
            if bowls:
                # مرتب‌سازی از چپ به راست
                bowls.sort(key=lambda c: cv2.boundingRect(c)[0])
                
                # رنگ‌آمیزی هر کاسه
                for i, bowl in enumerate(bowls[:3]):  # حداکثر 3 کاسه
                    # ایجاد ماسک
                    mask = np.zeros_like(frame)
                    cv2.drawContours(mask, [bowl], -1, (255,255,255), -1)
                    
                    # اعمال رنگ
                    color_layer = np.zeros_like(frame)
                    color_layer[:] = colors[i % len(colors)]
                    colored = cv2.bitwise_and(color_layer, mask)
                    
                    # ترکیب با تصویر اصلی
                    frame = cv2.addWeighted(frame, 1, colored, 0.7, 0)
            
            out.write(frame)
        
        cap.release()
        out.release()
        return output_path
        
    except Exception as e:
        logger.error(f"خطا در پردازش ویدیو: {e}")
        raise

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🤖 ربات تشخیص کاسه فعال شد! یک ویدیو ارسال کنید.")

@bot.message_handler(content_types=['video'])
def handle_video(message):
    try:
        # دریافت ویدیو
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # ذخیره موقت
        input_path = 'input.mp4'
        with open(input_path, 'wb') as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, "🔍 در حال پردازش ویدیو...")
        
        # پردازش ویدیو
        output_path = process_video(input_path)
        
        # ارسال نتیجه
        with open(output_path, 'rb') as video_file:
            bot.send_video(message.chat.id, video_file, caption="✅ پردازش انجام شد!")
        
        # پاکسازی فایل‌های موقت
        os.remove(input_path)
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        bot.reply_to(message, f"❌ خطا در پردازش: {str(e)}")

if __name__ == '__main__':
    logger.info("ربات در حال راه‌اندازی...")
    bot.polling()
