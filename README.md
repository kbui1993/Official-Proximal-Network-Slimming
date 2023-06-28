# Official-Proximal-Network-Slimming

This repository is an extension of the repository of [Network Slimming (Pytorch)](https://github.com/Eric-mingjie/network-slimming), an official pytorch implementation of the following paper:
[Learning Efficient Convolutional Networks Through Network Slimming](http://openaccess.thecvf.com/content_iccv_2017/html/Liu_Learning_Efficient_Convolutional_ICCV_2017_paper.html) (ICCV 2017).  

This repository proposes a new proximal algorithm to perform Network Slimming, where it
trains the CNN towards a sparse, accurate model. As a result, fine-tuning is an optional
step.

Citation:
```
@InProceedings{Liu_2017_ICCV,
    author = {Liu, Zhuang and Li, Jianguo and Shen, Zhiqiang and Huang, Gao and Yan, Shoumeng and Zhang, Changshui},
    title = {Learning Efficient Convolutional Networks Through Network Slimming},
    booktitle = {The IEEE International Conference on Computer Vision (ICCV)},
    month = {Oct},
    year = {2017}
}
```

You can refer to `script.sh` for examples to train and prune a CNN.



## Training

The `dataset` argument specifies which dataset to use: `cifar10` or `cifar100`. The `arch` argument specifies the architecture to use: `vgg`,`resnet` or `densenet`. The depth is chosen to be the same as the networks used in the paper. The `s` parameter is the regularization parameter for the L1 norm. The `beta` parameter is the quadratic penalty term.
```shell
python main.py -sr --s 0.0045 --dataset cifar10 --arch vgg --depth 19 --beta 100 --name [MODEL_NAME] --save [DIRECTORY TO SAVE MODEL]
```

## Prune

```shell
python vgg_prune_analyze.py --dataset cifar10 --depth 19 --percent 0.0 --model [NAME OF MODEL TO BE PRUNED] --save [DIRECTORY TO SAVE PRUNED MODEL]
```
The pruned model will have `pruned.pth.tar` at the end of its name.

## Fine-tune

```shell
python main.py --refine logs/vggnetpruned.pth.tar --dataset cifar10 --arch vgg --depth 19 --epochs 160 --name [REFINED_MODEL_NAME] --save [DIRECTORY TO SAVE MODEL]
```


## Dependencies
torch v0.3.1, torchvision v0.2.0