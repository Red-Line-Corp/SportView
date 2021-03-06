import cv2
import numpy as np
import os, shutil
from PIL import ImageFont, ImageDraw, Image  
from imutils.video import FPS
from dearpygui.core import *
from dearpygui.simple import *
from dearpygui.demo import *
from typing import cast
from pyguiStyle import load_def_style

def SvuotaCache():
    for filename in os.listdir("./src/cache"):
        file_path = os.path.join("./src/cache", filename)                
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)

def LoadImage(sender, data):
    SvuotaCache()
    video_capture = cv2.VideoCapture(data[0] + "/" + data[1]) #ottengo il video dal percorso selezionato
    width= int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height= int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    writer= cv2.VideoWriter('./risultati/risultato.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20, (width,height))
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    fps = FPS().start()
    with window("Preview"): #creo una finesta pygui dove mostrare il video     
        add_drawing("Immagine (nome file)")
        index = 0 #usato per cache
        while(True):            
            try:
                re,img = video_capture.read() #ottengo un frame
                if(not re):
                    break
                height, width, channels = img.shape

                blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)
                    #Detecting objects
                net.setInput(blob)
                outs = net.forward(output_layers)

                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                #colore del campo
                l_campo=np.array([40,40, 40])
                u_campo=np.array([70, 255, 255])
                m_campo=cv2.inRange(hsv, l_campo, u_campo)
                #colore squadra 1
                l_squadra1 = np.array([110,50,50])
                u_squadra1 = np.array([130,255,255])
                m_squadra1=cv2.inRange(hsv, l_squdra1, u_squadra1)
                #colore squadra 2
                l_squadra2=np.array([0,31,255])
                u_squadra2=np.array([176,255,255])
                m_squadra2=cv2.inRange(hsv, l_squadra2, u_squadra2)
                #bianco
                l_bianco = np.array([0,0,0])
                u_bianco = np.array([0,0,255])
                m_bianco=cv2.inRange(hsv, l_bianco, u_bianco)

                res = cv2.bitwise_and(img, img, mask=mask)
	            #convert to hsv to gray
                res_bgr = cv2.cvtColor(res,cv2.COLOR_HSV2BGR)
                res_gray = cv2.cvtColor(res,cv2.COLOR_BGR2GRAY)

                #Defining a kernel to do morphological operation in threshold image to 
                #get better output.
                kernel = np.ones((13,13),np.uint8)
                thresh = cv2.threshold(res_gray,127,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
	

                #find contours in threshold image     
                contours,hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                
                
                # Showing informations on the screen
                class_ids = []
                confidences = []
                boxes = []
                for out in outs:
                    for detection in out:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.7:
                            # Object detected
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)

                            # Rectangle coordinates
                            x = int(detection[0] * width - w / 2)
                            y = int(detection[1] * height - h / 2)

                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)
                
                #We use NMS function in opencv to perform Non-maximum Suppression
                #we give it score threshold and nms threshold as arguments.
                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
                font = cv2.FONT_HERSHEY_TRIPLEX
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]
                        color = colors[class_ids[i]]
                        cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
                        cv2.putText(img, str(classes[class_ids[i]]), (x, y + 30), font, 2, color, 3)


                for c in contours:
                    x,y,w,h = cv2.boundingRect(c)
		
		#Detect players
        if(h>=(1.5)*w):
			if(w>15 and h>= 15):
				idx = idx+1
				player_img = img[y:y+h,x:x+w]
				player_hsv = cv2.cvtColor(player_img,cv2.COLOR_BGR2HSV)
				#If player has blue jersy
				mask1 = cv2.inRange(player_hsv, l_squadra1, u_squadra1)
				res1 = cv2.bitwise_and(player_img, player_img, mask=mask1)
				res1 = cv2.cvtColor(res1,cv2.COLOR_HSV2BGR)
				res1 = cv2.cvtColor(res1,cv2.COLOR_BGR2GRAY)
				nzCount = cv2.countNonZero(res1)
				#If player has red jersy
				mask2 = cv2.inRange(player_hsv, l_squadra2, u_squadra2)
				res2 = cv2.bitwise_and(player_img, player_img, mask=mask2)
				res2 = cv2.cvtColor(res2,cv2.COLOR_HSV2BGR)
				res2 = cv2.cvtColor(res2,cv2.COLOR_BGR2GRAY)
				nzCountred = cv2.countNonZero(res2)

				if(nzCount >= 20):
					#Mark blue jersy players as france
					cv2.putText(img, 'France', (x-2, y-2), font, 0.8, (255,0,0), 2, cv2.LINE_AA)
					cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),3)
				else:
					pass
				if(nzCountred>=20):
					#Mark red jersy players as belgium
					cv2.putText(img, 'Belgium', (x-2, y-2), font, 0.8, (0,0,255), 2, cv2.LINE_AA)
					cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),3)
				else:
					pass
		if((h>=1 and w>=1) and (h<=30 and w<=30)):
			player_img = img[y:y+h,x:x+w]
		
			player_hsv = cv2.cvtColor(player_img,cv2.COLOR_BGR2HSV)
			#white ball  detection
			mask1 = cv2.inRange(player_hsv, l_bianco, u_bianco)
			res1 = cv2.bitwise_and(player_img, player_img, mask=mask1)
			res1 = cv2.cvtColor(res1,cv2.COLOR_HSV2BGR)
			res1 = cv2.cvtColor(res1,cv2.COLOR_BGR2GRAY)
			nzCount = cv2.countNonZero(res1)
	

			if(nzCount >= 3):
				# detect football
				cv2.putText(img, 'football', (x-2, y-2), font, 0.8, (0,255,0), 2, cv2.LINE_AA)
				cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,0),3)
        

                writer.write(img)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break




                cv2.imwrite("./src/cache/{0}_{1}_cache.jpg".format(index, data[1]), img) #salvo il frame nella cache
                img = cv2.resize(img, None, fx=1.0, fy=1.0) #non usato (ridimensiona l`immagine)

                height, width, _ = img.shape #imposto la dimensione della finestra preview in base al video
                set_item_height("Preview", height + 20)
                set_item_height("Immagine (nome file)", height)
                set_item_width("Preview", width + 20)
                set_item_width("Immagine (nome file)", width)

                draw_image("Immagine (nome file)", "./src/cache/{0}_{1}_cache.jpg".format(index, data[1]), [0, 0], [width, height]) #carico il frame dalla cache
               
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                if(index > 2):
                    os.remove("./src/cache/{0}_{1}_cache.jpg".format(index - 2, data[1])) #elimino il file inutile dalla cache
                index = index + 1
                fps.update()
            except:
                SvuotaCache()
                video_capture.release()
                fps.stop()
                writer.release()
                return
        SvuotaCache()
        video_capture.release()           
        fps.stop()
        writer.release()
        print("{:.2f}".format(fps.fps()))

def BtnFileSelectClick():
    #TODO custom extensions
    open_file_dialog(LoadImage)

# Load Yolo
print("LOADING YOLO")
net = cv2.dnn.readNet("./cfg/yoloV3.weights", "./cfg/yoloV3.cfg")

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

#save all the names in file o the list classes
classes = []
with open("./cfg/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]
#get layers of the network
layer_names = net.getLayerNames()
#Determine the output layer names from the YOLO model 
output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
print("YOLO LOADED")

# #rilevazione
# #video_capture = cv2.VideoCapture("resources/prova.avi")
# video_capture = cv2.VideoCapture("C:/Users/claud/Desktop/Film Role-0 ID-6 T-2 m00s00-000-m00s00-185.mp4")
# width= int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
# height= int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
# #writer= cv2.VideoWriter('risultati/risultato.avi', cv2.VideoWriter_fourcc(*'DIVX'), 20, (width,height))
# writer= cv2.VideoWriter('risultati/risultato.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 20, (width,height))

# colors = np.random.uniform(0, 255, size=(len(classes), 3))
# fps = FPS().start()
# while True:
#    # Capture frame-by-frame
#     re,img = video_capture.read()
#     if(not re):
#        break
#     height, width, channels = img.shape

#     # USing blob function of opencv to preprocess image
#     blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)
#     #Detecting objects
#     net.setInput(blob)
#     outs = net.forward(output_layers)

#     # Showing informations on the screen
#     class_ids = []
#     confidences = []
#     boxes = []
#     for out in outs:
#         for detection in out:
#             scores = detection[5:]
#             class_id = np.argmax(scores)
#             confidence = scores[class_id]
#             if confidence > 0.7:
#                 # Object detected
#                w = int(detection[2] * width)
#                h = int(detection[3] * height)

#                 # Rectangle coordinates
#                x = int(detection[0] * width - w / 2)
#                y = int(detection[1] * height - h / 2)

#                boxes.append([x, y, w, h])
#                confidences.append(float(confidence))
#                class_ids.append(class_id)
    
#     #We use NMS function in opencv to perform Non-maximum Suppression
#     #we give it score threshold and nms threshold as arguments.
#     indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
#     font = cv2.FONT_HERSHEY_TRIPLEX
#     for i in range(len(boxes)):
#         if i in indexes:
#             x, y, w, h = boxes[i]
#             color = colors[class_ids[i]]
#             cv2.rectangle(img, (x, y), (x + w, y + h), color, 2)
#             cv2.putText(img, str(classes[class_ids[i]]), (x, y + 30), font, 2, color, 3)

#     writer.write(img)

#     cv2.imshow("Image", img)
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break
#     fps.update()
# fps.stop()



# video_capture.release()
# writer.release()

enable_docking(shift_only = False)
set_main_window_size(1920, 1080)
set_main_window_title("SportView")

add_additional_font("./resources/fonts/Poppins/Poppins-Medium.ttf", size = 15.0)

load_def_style()

with window("Docking canvas", width = 1920, height = 1080, no_move = True, no_resize = True, no_background = True, no_title_bar=True, x_pos = 0, y_pos = 0, no_bring_to_front_on_focus = True):
    set_primary_window("Docking canvas", True)

with window("File"):
    add_button("Select a file", callback = BtnFileSelectClick)
    add_button("Download", callback = BtnFileSelectClick)

start_dearpygui()
stop_dearpygui()