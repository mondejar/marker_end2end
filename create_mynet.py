# Caffe Example:
# http://nbviewer.jupyter.org/github/BVLC/caffe/blob/master/examples/01-learning-lenet.ipynb

caffe_root = '/home/mondejar/caffe-master/'  # this file should be run from {caffe_root}/examples (otherwise change this line)

import sys
sys.path.insert(0, caffe_root + 'python')
import caffe
from caffe import layers as L, params as P


def my_net(data_train_lmdb, label_train_lmdb, data_val_lmdb, label_val_lmdb, batch_size):
    # our version of LeNet: a series of linear and simple nonlinear transformations
    n = caffe.NetSpec()
    
    n.data = L.Data(name='data', batch_size=batch_size, backend=P.Data.LMDB, 
        source=data_train_lmdb, ntop=1, transform_param=dict(scale=1./255), include={'phase':caffe.TRAIN})  #, transform_param=dict(scale=1./255) 

    n.label = L.Data(batch_size=batch_size, backend=P.Data.LMDB, 
        source=label_train_lmdb, ntop=1,include={'phase':caffe.TRAIN}) 

    n.test_data = L.Data(name='data', batch_size=batch_size, backend=P.Data.LMDB, 
        source=data_val_lmdb, ntop=1, transform_param=dict(scale=1./255), include={'phase':caffe.TEST})   #transform_param=dict(scale=1./255) 

    n.test_label  = L.Data(batch_size=batch_size, backend=P.Data.LMDB,
        source=label_val_lmdb, ntop=1, include={'phase':caffe.TEST}) 

    n.conv1 = L.Convolution(n.data, kernel_size=5, num_output=32, weight_filler=dict(type='xavier')) 
    n.relu1 = L.ReLU(n.conv1, in_place=True)

    #n.conv2 = L.Convolution(n.conv1,kernel_size=5, num_output=32, weight_filler=dict(type='xavier'))
    #n.pool2 = L.Pooling(n.conv2,    kernel_size=3, stride=2, pool=P.Pooling.MAX)

    n.conv3 = L.Convolution(n.conv1,kernel_size=5, num_output=32, weight_filler=dict(type='xavier'))
    n.relu3 = L.ReLU(n.conv3, in_place=True)

    #n.conv4 = L.Convolution(n.conv3,kernel_size=5, num_output=32, weight_filler=dict(type='xavier'))
    n.pool4 = L.Pooling(n.conv3,    kernel_size=3, stride=2, pool=P.Pooling.MAX)

    n.conv5 = L.Convolution(n.pool4,kernel_size=3, num_output=64, weight_filler=dict(type='xavier'))
    n.relu5 = L.ReLU(n.conv5, in_place=True)

    n.conv6 = L.Convolution(n.conv5,kernel_size=3, num_output=64, weight_filler=dict(type='xavier'))
    n.relu6 = L.ReLU(n.conv6, in_place=True)
    
    n.pool6 = L.Pooling(n.conv6,    kernel_size=3, stride=2, pool=P.Pooling.MAX)

    n.conv7 = L.Convolution(n.pool6,kernel_size=3, num_output=64, weight_filler=dict(type='xavier'))
    n.relu7 = L.ReLU(n.conv7, in_place=True)

    n.conv8 = L.Convolution(n.conv7,kernel_size=3, num_output=64, weight_filler=dict(type='xavier'))
    n.relu8 = L.ReLU(n.conv8, in_place=True)

    n.drop8 = L.Dropout(n.conv8, in_place=True, dropout_ratio= 0.5)
    # Dropout

    #n.fc1 =   L.InnerProduct(n.conv7, num_output=1024, weight_filler=dict(type='xavier'))
    n.fc1 =   L.InnerProduct(n.drop8, num_output=256, weight_filler=dict(type='xavier'))
    #n.relu9 = L.ReLU(n.fc1, in_place=True)
    n.score = L.InnerProduct(n.drop8, num_output=8, weight_filler=dict(type='xavier'))

    n.loss =  L.EuclideanLoss(n.score, n.label)


    # TODO  test_data and test_label to data and label.... phase TEST

    return n.to_proto()
    
with open('/home/mondejar/markers_end2end/my_net_auto_train.prototxt', 'w') as f:
    marker_size = 128
    batch_size = 1
    lmdb_dir_tr  = '/home/mondejar/markers_end2end/LMDB/' + str(marker_size) + '/training'
    lmdb_dir_val = '/home/mondejar/markers_end2end/LMDB/' + str(marker_size) + '/validation'

    f.write(str(my_net(lmdb_dir_tr + '/markers_img_LMDB', lmdb_dir_tr + '/markers_labels_LMDB',
        lmdb_dir_val + '/markers_img_LMDB', lmdb_dir_val + '/markers_labels_LMDB', batch_size)))
    
