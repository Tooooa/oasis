# -*- coding: utf-8 -*-
"""
r/TechFuture 种子数据
5个初始帖子 + 每帖2-3条评论
"""

SEED_POSTS = [
    {
        "title": "AI 对程序员就业的影响",
        "content": """随着 AI 编程助手（如 GitHub Copilot、Cursor）的快速普及，程序员的就业形势正在发生变化。

一方面，AI 工具让开发效率大幅提升；另一方面，有人担心初级开发岗位会被取代。

大家怎么看？AI 是程序员的好帮手，还是潜在的竞争者？""",
        "initial_comments": [
            {
                "content": "我觉得初级岗位确实会受影响，但高级架构师和系统设计师反而更重要了。AI 能写代码，但不能做决策。",
                "upvotes": 15
            },
            {
                "content": "AI 只是工具，关键还是解决问题的能力。会用 AI 的程序员 vs 不会用的，差距会越来越大。",
                "upvotes": 23
            }
        ]
    },
    {
        "title": "SpaceX 火星计划的现实性",
        "content": """Starship 最近的测试进展令人印象深刻，成功实现了筷子回收。

但 Elon Musk 提出的 2030 年载人登陆火星目标真的可行吗？技术、成本、人体健康风险...挑战似乎无处不在。

你觉得人类什么时候能真正踏上火星？""",
        "initial_comments": [
            {
                "content": "技术上我觉得是可行的，但成本和风险仍然巨大。NASA 的保守 timeline 可能更现实一些。",
                "upvotes": 12
            },
            {
                "content": "我更关心的是火星殖民的伦理问题。谁有权决定谁去？资源怎么分配？这些问题比技术更难解决。",
                "upvotes": 8
            },
            {
                "content": "SpaceX 的迭代速度确实惊人。5年前没人想到可重复使用火箭能做到现在这样。",
                "upvotes": 18
            }
        ]
    },
    {
        "title": "Web3 是否已经死亡？",
        "content": """加密货币市场持续低迷，NFT 热度消退到冰点，多个知名 Web3 项目倒闭...

两年前的 Web3 狂热仿佛就在昨天，但现在似乎已经没人谈论了。

Web3 真的已经死了吗？还是只是在泡沫破裂后寻找真正的应用场景？""",
        "initial_comments": [
            {
                "content": "炒作是死了，但底层的区块链技术还在稳步发展。DeFi 和 跨境支付还是有实际价值的。",
                "upvotes": 14
            },
            {
                "content": "说实话，我觉得就是一个泡沫。现在该破了。真正有价值的技术不需要这么多炒作。",
                "upvotes": 21
            }
        ]
    },
    {
        "title": "新款 VR 设备测评：Vision Pro 值得买吗？",
        "content": """Apple Vision Pro 发布已经快一年了。作为一个早期用户，我想分享一些真实使用体验。

优点：视觉效果惊艳、手势交互自然、生态整合优秀
缺点：价格昂贵、佩戴舒适度一般、杀手级应用缺乏

VR/AR 市场会因为 Apple 的入局而改变吗？你们觉得值得入手吗？""",
        "initial_comments": [
            {
                "content": "2.5万的价格太贵了，普通消费者根本接受不了。等二代降价再说吧。",
                "upvotes": 25
            },
            {
                "content": "体验确实惊艳，但应用生态是个大问题。没有足够的 killer app，再好的硬件也白搭。",
                "upvotes": 16
            },
            {
                "content": "我觉得这更像是开发者预览版，不是消费级产品。Apple 在布局未来。",
                "upvotes": 11
            }
        ]
    },
    {
        "title": "开源模型 vs 闭源模型：谁是 AI 的未来？",
        "content": """Llama 3、Mistral、Qwen 等开源模型进步神速，与 GPT-4、Claude 的差距在快速缩小。

开源阵营主张透明、可控、社区驱动；
闭源阵营强调安全、性能、商业可持续。

你更看好哪一边？企业应该选择开源还是闭源模型？""",
        "initial_comments": [
            {
                "content": "开源模型进步确实很快，但顶尖推理能力还有差距。不过对于大多数应用场景，开源已经够用了。",
                "upvotes": 19
            },
            {
                "content": "对于企业来说，数据安全和可控性更重要。开源模型本地部署是趋势。",
                "upvotes": 22
            }
        ]
    }
]


def get_seed_post_actions():
    """
    生成种子帖子的 ManualAction 列表
    返回初始化环境所需的动作列表
    """
    actions = []
    for post in SEED_POSTS:
        actions.append({
            "type": "CREATE_POST",
            "content": f"【{post['title']}】\n\n{post['content']}"
        })
    return actions


def get_initial_comment_actions():
    """
    生成初始评论的 ManualAction 列表
    post_id 从 1 开始
    """
    actions = []
    for post_id, post in enumerate(SEED_POSTS, start=1):
        for comment in post["initial_comments"]:
            actions.append({
                "type": "CREATE_COMMENT",
                "post_id": post_id,
                "content": comment["content"]
            })
    return actions
