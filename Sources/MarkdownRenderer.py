import json, os

class MarkdownRenderer:
    def Render(self, day, recommendations):
        markdownLines = [f"## 每日论文推荐 — {day}\n"]

        for paper in recommendations:
            markdownLines.append(
                f"- **{paper['title']}**\n"
                f"  - 发表日期：{paper.get('date', '')} | 推荐度：{paper['Similarity']:.3f} | 来源：{paper.get('source','')}\n"
                f"  - DOI：{paper.get('doi', '')}\n"
                f"  - 链接：{paper.get('url','')}\n"
                f"  - 摘要：{paper.get('abstract','')}\n"
            )
            
        markdown = "\n".join(markdownLines)
        os.makedirs("outputs", exist_ok = True)
        with open(f"outputs/daily_{day}.md","w",encoding="utf-8") as f:
            f.write(markdown)

        return markdown
