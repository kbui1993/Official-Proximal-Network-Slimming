python main.py -sr --s 0.0045 --dataset cifar10 --arch vgg --depth 19 --beta 100 --name vgg_L1_0pt0045 --save logs
python vgg_prune_analyze.py --dataset cifar10 --depth 19 --percent 0.0 --model logs/vgg_L1_0pt0045_vgg_19_cifar10model_best.pth.tar --save logs
python main.py --refine logs/vggnetpruned.pth.tar --dataset cifar10 --arch vgg --depth 19 --epochs 160 --name vgg_refined_cifar10 --save logs

# python main.py -sr --s 0.004 --dataset cifar10 --arch densenet --depth 40 --beta 100 --name densenet_L1_0pt004 --save logs
# python denseprune_analyze.py --dataset cifar10 --depth 40 --percent 0.0 --model logs/densenet_L1_0pt004_densenet_40_cifar10model_best.pth.tar --save logs
# python main.py --refine logs/densenetpruned.pth.tar --dataset cifar10 --arch densenet --depth 40 --epochs 160 --name densenet_refined_cifar10 --save logs

# python main.py -sr --s 0.002 --dataset cifar10 --arch resnet --depth 164 --beta 0.25 --name resnet164_L1_0pt002 --save logs
# python resprune_analyze.py --dataset cifar10 --depth 164 --percent 0.0 --model logs/resnet164_L1_0pt002_resnet_164_cifar10model_best.pth.tar --save logs
# python main.py --refine logs/ResNetpruned.pth.tar --dataset cifar10 --arch resnet --depth 164 --epochs 160 --name resnet_refined_cifar10 --save logs