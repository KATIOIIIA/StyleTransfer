import random

from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms

import copy

from torchvision import models

from ContentLoss import ContentLoss
from Normalization import Normalization
from StyleLoss import StyleLoss
import asyncio
from config import NUM_STEPS, STYLE_WEIGHT, CONTENT_WEIGHT, DEF_IMSIZE


class StyleTransferModel(object):
    def __init__(self, fileNameStyle, fileNameImage):

        self.num_steps = NUM_STEPS
        self.style_weight = STYLE_WEIGHT
        self.content_weight = CONTENT_WEIGHT
        self.imsize = DEF_IMSIZE
        self.content_layers_default = ['conv_4']
        self.style_layers_default = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

        self.loader = transforms.Compose([
            transforms.Resize(self.imsize),  # нормируем размер изображения
            transforms.CenterCrop(self.imsize),
            transforms.ToTensor()])  # превращаем в удобный формат

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.style_img = self.image_loader(fileNameStyle)
        self.content_img = self.image_loader(fileNameImage)
        self.input_img = self.content_img.clone()

        self.cnn_normalization_mean = torch.tensor([0.485, 0.456, 0.406]).to(self.device)
        self.cnn_normalization_std = torch.tensor([0.229, 0.224, 0.225]).to(self.device)
        # self.cnn = models.vgg19(pretrained=True).features.to(self.device).eval()
        self.cnn = torch.load('model/vgg19.pth').to(self.device).eval()

    def image_loader(self, download_file):
        image = Image.open(download_file)
        image = self.loader(image).unsqueeze(0)
        return image.to(self.device, fl)

    def gram_matrix(self, input):
        batch_size, h, w, f_map_num = input.size()  # batch size(=1)
        # b=number of feature maps
        # (h,w)=dimensions of a feature map (N=h*w)
        features = input.view(batch_size * h, w * f_map_num)  # resise F_XL into \hat F_XL
        G = mm(features, features.t())  # compute the gram product
        # we 'normalize' the values of the gram matrix
        # by dividing by the number of element in each feature maps.
        return G.div(batch_size * h * w * f_map_num)

    def get_style_model_and_losses(self):
        cnn = copy.deepcopy(self.cnn)

        content_layers = self.content_layers_default
        style_layers = self.style_layers_default
        # normalization module
        normalization = Normalization(self.cnn_normalization_mean, self.cnn_normalization_std).to(self.device)

        # just in order to have an iterable access to or list of content/syle
        # losses
        content_losses = []
        style_losses = []

        # assuming that cnn is a nn.Sequential, so we make a new nn.Sequential
        # to put in modules that are supposed to be activated sequentially
        model = nn.Sequential(normalization)

        i = 0  # increment every time we see a conv
        for layer in cnn.children():
            if isinstance(layer, nn.Conv2d):
                i += 1
                name = 'conv_{}'.format(i)
            elif isinstance(layer, nn.ReLU):
                name = 'relu_{}'.format(i)
                # The in-place version doesn't play very nicely with the ContentLoss
                # and StyleLoss we insert below. So we replace with out-of-place
                # ones here.
                # Переопределим relu уровень
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = 'pool_{}'.format(i)
            elif isinstance(layer, nn.BatchNorm2d):
                name = 'bn_{}'.format(i)
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            model.add_module(name, layer)

            if name in content_layers:
                # add content loss:
                target = model(self.content_img).detach()
                content_loss = ContentLoss(target)
                model.add_module("content_loss_{}".format(i), content_loss)
                content_losses.append(content_loss)

            if name in style_layers:
                # add style loss:
                target_feature = model(self.style_img).detach()
                style_loss = StyleLoss(target_feature)
                model.add_module("style_loss_{}".format(i), style_loss)
                style_losses.append(style_loss)

        # now we trim off the layers after the last content and style losses
        # выбрасываем все уровни после последенего styel loss или content loss
        for i in range(len(model) - 1, -1, -1):
            if isinstance(model[i], ContentLoss) or isinstance(model[i], StyleLoss):
                break

        model = model[:(i + 1)]

        return model, style_losses, content_losses

    def get_input_optimizer(self, input_img):
        # this line to show that input is a parameter that requires a gradient
        # добоваляет содержимое тензора катринки в список изменяемых оптимизатором параметров
        optimizer = optim.LBFGS([input_img.requires_grad_()], lr=0.1)
        return optimizer

    async def run_style_transfer(self):
        """Run the style transfer."""
        print('Building the style transfer model..')
        model, style_losses, content_losses = self.get_style_model_and_losses()
        optimizer = self.get_input_optimizer(self.input_img)

        print('Optimizing..')
        run = [0]
        while run[0] <= self.num_steps:

            await asyncio.sleep(random.randint(0, 5))

            def closure():
                # correct the values
                # это для того, чтобы значения тензора картинки не выходили за пределы [0;1]
                self.input_img.data.clamp_(0, 1)

                optimizer.zero_grad()

                model(self.input_img)

                style_score = 0
                content_score = 0

                for sl in style_losses:
                    style_score += sl.loss
                for cl in content_losses:
                    content_score += cl.loss

                # взвешивание ощибки
                style_score *= self.style_weight
                content_score *= self.content_weight

                loss = style_score + content_score
                loss.backward()

                run[0] += 1

                if run[0] % 50 == 0:
                    print("run {}:".format(run))
                    print('Style Loss : {:4f} Content Loss: {:4f}'.format(
                        style_score.item(), content_score.item()))
                    print()

                return style_score + content_score

            optimizer.step(closure)

        # a last correction...
        self.input_img.data.clamp_(0, 1)

        return self.input_img


'''
fileNameStyle = "images/style.jpg"
fileNameImage = "images/IMG.jpg"
ST_model = StyleTransferModel(fileNameStyle, fileNameImage)

output = ST_model.run_style_transfer()

save_image(output, 'img1.png')
'''
