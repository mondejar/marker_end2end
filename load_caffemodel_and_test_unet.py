# Code for load the trained file .caffemodel
# and feed the model with inputs to check the output generated by the model

caffe_root = '/home/mondejar/caffe-master/'  # this file should be run from {caffe_root}/examples (otherwise change this line)

import sys
sys.path.insert(0, caffe_root + 'python')
import caffe
from caffe import layers as L, params as P

import cv2
from draw_corners_on_marker import *

verbose = 2


marker_size = 64#128
model_dir = '/home/mondejar/markers_end2end/'
model_filename = model_dir + 'caffe/my_net_iter_55000.caffemodel'
prototxt_filename = model_dir + 'my_unet.prototxt'

caffe.set_device(0)
caffe.set_mode_gpu()

net = caffe.Net(prototxt_filename, model_filename, caffe.TEST)

num_batches = 1000
batch_size = 1

export_dir = '/home/mondejar/Dropbox/markers_results/'
for n in range(0, num_batches):
    net.forward() # this will load the next mini-batch as defined in the net

    for b in range(0, batch_size):
        im_gt = np.array(net.blobs['label'].data[b].reshape(marker_size, marker_size) * 255.0, dtype=np.float32) #dtype=np.uint8) 

        # Draw Output
        # two chanels
        #im = np.array(net.blobs['data'].data[b].reshape(2, marker_size, marker_size) * 255.0, dtype=np.uint8) 
        im = np.array(net.blobs['data'].data[b].reshape(marker_size, marker_size) * 255.0, dtype=np.float32)
        
        im_pred = np.array(net.blobs['conv12'].data[b].reshape(marker_size, marker_size) * 255.0, dtype=np.float32)
        #im = np.array(net.blobs['data'].data[b].reshape(marker_size, marker_size) * 255.0, dtype=np.uint8) 
        #im_pred = draw_corners_on_marker(im, predicted_coor * float(marker_size))

        im_show = cv2.cvtColor(im,cv2.COLOR_GRAY2RGB)
        im_show[:,:,1] = im_pred
        cv2.imwrite(export_dir + 'marker_' + str(n) + '_pred.png', im_show)

        #cv2.imwrite(export_dir + 'marker_' + str(n) + '.png', im) #[0]
        #cv2.imwrite(export_dir + 'marker_' + str(n) + '_gt.png', im_gt)   
        #cv2.imwrite(export_dir + 'marker_' + str(n) + '_pred.png', im_pred)

        # TODO fuse both images??

        # Display
        """
        if verbose > 1:
            cv2.namedWindow('img', cv2.WINDOW_NORMAL)
            cv2.imshow('img', im)

            cv2.namedWindow('im_gt', cv2.WINDOW_NORMAL)
            cv2.imshow('im_gt', im_gt )

            cv2.namedWindow('im_pred', cv2.WINDOW_NORMAL)
            cv2.imshow('im_pred', im_pred)
            print(im_pred)
            key = cv2.waitKey(0)
            
            if key == 27:    # Esc key to stop
                sys.exit(0)
            
            cv2.destroyAllWindows()
        """