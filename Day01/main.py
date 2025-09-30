"""恐怖のテキストアドベンチャーゲーム。

Python の基本文法（変数・関数・条件分岐・ループ）を復習しながら、
プレイヤーの選択によって結末が変化するホラー体験を提供します。
ゲームは標準入力（キーボード）から操作します。
"""

from __future__ import annotations  # 将来の Python バージョンとの互換性を高めるための宣言

import random  # 乱数を扱う標準ライブラリ。選択結果に揺らぎを与えるのに使用する。
import textwrap  # 長い文章を自動的に折り返すための標準ライブラリ。
from dataclasses import dataclass  # ゲームの状態を管理するためのデータクラスを定義する。


# =============================
# ゲーム設定（定数）
# =============================
# 定数は全て大文字で書くのが Python の慣習です。
INTRO_TEXT = """
深夜 2 時。豪雨の中、あなたは古びた洋館に足止めされてしまった。
窓の向こうでは稲妻が走り、耳鳴りのような囁き声が聞こえてくる。
玄関は固く閉ざされ、助けを求める手段は無い。ここから生きて出られるだろうか……。
"""

ROOMS = (
    "血塗られた玄関ホール",
    "曲がりくねった廊下",
    "鏡張りの応接室",
    "地下へ続く螺旋階段",
)

FINAL_EVENTS = (
    "あなたは鏡の中の影に呑み込まれ、永遠に閉じ込められた……",
    "突如響いた鐘の音と共に、館の主が背後に現れた。逃げ場はない。",
    "地下室で見つけた扉の先は底なしの闇だった。落下する感覚だけが残る。",
)

# random.choice() に渡すリスト。成功と失敗のどちらに転ぶか、確率を少しだけ傾ける。
SUCCESS_TABLE = [True, False, False]


@dataclass
class PlayerState:
    """プレイヤーの状態を表すデータクラス。

    データクラスは、値をまとめて管理するためのシンプルな仕組みです。
    フィールドを列挙するだけで __init__ などを自動生成してくれます。
    """

    courage: int = 3  # 所持している「勇気」。選択によって上下し、0 になるとゲームオーバー。
    clues: int = 0  # 集めた「手掛かり」の数。多いほど生還エンドに近づく。

    def is_alive(self) -> bool:
        """勇気が残っているかを判定するヘルパーメソッド。"""

        return self.courage > 0


# =============================
# ユーティリティ関数
# =============================

def slow_print(text: str) -> None:
    """文章を折り返しながら表示する関数。

    textwrap.dedent() で行頭のインデントを整理し、
    textwrap.fill() で 70 文字ごとに改行を挿入しています。
    """

    formatted = textwrap.fill(textwrap.dedent(text).strip(), width=70)
    print(formatted)


def prompt_choice(question: str, choices: tuple[str, ...]) -> int:
    """選択肢を表示し、ユーザーに番号入力を促す関数。

    Args:
        question: 質問文。
        choices: 選択肢（タプル）。インデックスが 0 から始まる点に注意。

    Returns:
        int: プレイヤーが選んだ選択肢のインデックス番号。
    """

    while True:  # 無限ループ（ただし return で抜ける）。
        slow_print(question)
        for index, label in enumerate(choices, start=1):
            print(f"  {index}. {label}")
        user_input = input("番号を入力してください: ")

        # str.isdigit() は文字列が数値のみで構成されているかを判定するメソッド。
        if user_input.isdigit():
            selected = int(user_input) - 1  # 人間は 1 始まりで数えるので -1 する。
            if 0 <= selected < len(choices):
                return selected

        print("入力が正しくありません。1 から {0} の番号を選んでください。".format(len(choices)))


def resolve_room(state: PlayerState, room_name: str) -> None:
    """各部屋で発生するイベントを処理する関数。"""

    slow_print(f"\n--- {room_name} ---")

    # 部屋ごとの演出と選択肢。
    slow_print(
        "壁に染みついた血痕が指し示す方向と、かすかなすすり泣きが聞こえる方向がある。"
    )
    action = prompt_choice(
        "どちらへ進みますか？",
        ("血痕を追う", "すすり泣きの元を探る", "祈りを捧げる"),
    )

    # if/elif/else は条件分岐。True になった最初のブロックが実行される。
    if action == 0:
        slow_print("壁に触れると冷たい感触が指を這い、勇気が吸い取られていく……")
        state.courage -= 1
    elif action == 1:
        slow_print("声の正体は同じく迷い込んだ旅人だった。共に脱出の手掛かりを探す。")
        state.clues += 1
    else:
        slow_print("呪文を唱えると、一瞬だけ影が怯んだ。だが代償にあなたの心が削られる。")
        state.courage -= 1
        state.clues += 1

    # 勇気が尽きた場合は、これ以上処理しない。
    if not state.is_alive():
        slow_print("恐怖に心が折れた……。あなたはその場に崩れ落ち、闇が覆い尽くす。")
        return

    # ランダムなノイズ演出。random.choice() で要素を 1 つ選ぶ。
    slow_print(random.choice(
        (
            "天井裏を何かが這う音がした。", 
            "背後で足音が止まった気がする……振り返る勇気はあるか？", 
            "遠くで鈴の音が鳴り、寒気が背筋を走る。",
        )
    ))

    # 低確率で追加イベント。
    if random.choice(SUCCESS_TABLE):
        slow_print("偶然見つけた日記に脱出のヒントが記されていた！")
        state.clues += 1
    else:
        slow_print("扉を開けるたびに同じ部屋に戻ってしまう……時間だけが奪われていく。")
        state.courage -= 1


def reach_finale(state: PlayerState) -> None:
    """ゲームの結末を決定して表示する関数。"""

    slow_print("\n--- 最終局面 ---")

    # 手掛かりが多く残っていれば生還。
    if state.clues >= 3 and state.is_alive():
        slow_print(
            "集めた手掛かりを組み合わせ、あなたは封じられた出口を見つけ出した！\n"
            "夜明けの光が差し込み、館は静かに崩れ落ちていく……あなたは生還した。"
        )
        return

    # ここまで来たが勇気が枯渇した場合はバッドエンド。
    if not state.is_alive():
        slow_print("恐怖に耐え切れず、その場で精神を手放してしまった……。")
        return

    # それ以外はランダムなホラーエンド。
    slow_print(random.choice(FINAL_EVENTS))


def main() -> None:
    """ゲーム全体の進行を管理するメイン関数。"""

    slow_print(INTRO_TEXT)
    state = PlayerState()

    # for ループで、ROOMS の要素を 1 つずつ処理する。
    for room in ROOMS:
        resolve_room(state, room)
        if not state.is_alive():  # 途中で勇気が尽きたらループを抜ける。
            break

    reach_finale(state)


if __name__ == "__main__":
    # Python スクリプトとして直接実行されたときだけ main() を呼び出す慣習的な書き方。
    main()
