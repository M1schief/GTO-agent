### 如何测试编辑后的 prompt 的效果

1. 将 ip.csv 和 oop.csv 放在 GTO-agent/llm_agent 目录下

2. 命令行导入 API-KEY

   ```
   export OPENAI_API_KEY="..."
   ```

3. 在 GTO-agent 根目录下运行（需安装一些依赖package）

   ```
   python llm_agent/llm.py
   ```

4. 输出在 GTO-agent/llm_agent 目录下的 outcome.txt 中。

5. (optional) 为了固定手牌，llm.py 第163行已注释。如需随机手牌，可以取消注释162行。