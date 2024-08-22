### Retrieval Augmented Generation 的测试报告

#### 1. RAG的原理

RAG的基本原理是以下三步：

1）**建库：**将用户提供的文档分割成 chunk，并编码成向量

2）**检索：**根据用户 prompt，检索向量数据库中最相关的前 k 个 chunk，共同形成本次的上下文。

3）**推理：**将新 prompt 输入到 LLM 中做推理

不同的 RAG 实现的区别主要在于前两步的算法设计。

#### 2. 使用 RAG 的三种方法

##### 2.1. Github开源项目 + API

使用开源项目的 RAG 实现，加上deepseek（或chatgpt3.5) API

https://github.com/QuivrHQ/quivr

https://github.com/infiniflow/ragflow

尚未有时间本地部署，不知道效果怎样。

##### 2.2. Github开源项目自己封装的 chatbot

https://github.com/infiniflow/ragflow

尝试了这个库自带的 online chatbot

数据库建立使用了英文版的 Phil Gordon's Little Green Book。这里只下载到了扫描版，能够成功通过编码，但是存在以下问题：

+ OCR 存在部分问题（可能是扫描版的问题）
+ 目录、页眉存在大量冗余chunk

+ 检索过程非常慢（算法固有问题？这里再 survey 一下有没有高效的版本）

效果上也完全不行，使用之前确定的格式化局面输入，检索不到相关chunk。然而一个较短的例子（How should I play when I flop a set?）可以成功匹配相关 chunk。推测问题是这个 chatbot 只能应对较短 prompt 在数据库中的匹配。

#####  2.3. 自带 RAG 功能的商用 chatbot

gpt3.5 不支持 RAG功能，gpt4 和 deepseek 声称支持 RAG 功能。

考虑价格实际试用了下 deepseek：

+ 不上传本地文件作为数据库时，似乎只是web检索一下数据库相关的简介，然后拼凑到回答中（这点似乎 gpt4 也是一样的）。
+ deepseek online chatbot 不支持上传本地文件，不确定 API 支不支持上传文件。

#### 3. 后续方向

首先，为保证推理的效率，数据库不能太大，最好是手工整理非常有限的材料或者现成的 manual、blog。这样同时也能保证数据库的格式，不产生太多坏 chunk。

在这个前提下，可以再尝试下前两种方法。

不过考虑一个小的数据库，在 context 长度已经能够上万的当下，是否能够直接放到上下文中（这样就没有了 RAG 的必要）？

这个问题，包括如何正确搭建一个高效的 RAG，需要再咨询下同学。