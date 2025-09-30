"""恐怖のテキストアドベンチャーゲーム。

Python の基本文法（変数・関数・条件分岐・ループ）を復習しながら、
プレイヤーの選択によって結末が変化するホラー体験を提供します。
ゲームは端末（コンソール）だけでなく、Tkinter を用いた簡易 GUI でも
操作できるように設計されています。
"""

from __future__ import annotations  # 将来の Python バージョンとの互換性を高めるための宣言

import os  # 実行環境（GUI が利用可能かどうか）を判定するために使用する。
import random  # 乱数を扱う標準ライブラリ。選択結果に揺らぎを与えるのに使用する。
import textwrap  # 長い文章を自動的に折り返すための標準ライブラリ。
from dataclasses import dataclass  # ゲームの状態を管理するためのデータクラスを定義する。
from typing import Iterable, Protocol  # インターフェースを記述し、型チェックを助ける。

try:
    import tkinter as tk  # GUI（グラフィカルユーザーインターフェース）を構築する標準ライブラリ。
except Exception:  # GUI を利用できない環境では ImportError や TclError が発生することがある。
    tk = None


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
# ユーティリティ関数およびインターフェース定義
# =============================

class GameInterface(Protocol):
    """ゲームの表示や入力を担当するインターフェース。"""

    def display(self, text: str) -> None:
        """文章を表示するためのメソッド。"""

    def choose(self, question: str, choices: tuple[str, ...]) -> int:
        """選択肢を提示し、選ばれたインデックスを返すメソッド。"""

    def on_game_end(self) -> None:
        """ゲーム終了時に呼び出されるフック。"""


def format_paragraphs(text: str, width: int = 70) -> Iterable[str]:
    """文章を段落単位で整形し、表示しやすい形にして返す。"""

    cleaned = textwrap.dedent(text).strip().splitlines()
    for line in cleaned:
        if line.strip():
            yield textwrap.fill(line, width=width)
        else:
            yield ""


def slow_print(text: str) -> None:
    """文章を折り返しながら表示する関数。"""

    for paragraph in format_paragraphs(text):
        print(paragraph)
    print()  # 空行を挿入して読みやすさを向上させる。


class ConsoleInterface:
    """端末上でゲームを進めるための実装。"""

    def display(self, text: str) -> None:
        """テキストを折り返して表示する。"""

        slow_print(text)

    def choose(self, question: str, choices: tuple[str, ...]) -> int:
        """選択肢を表示し、番号入力を受け取る。"""

        while True:
            self.display(question)
            for index, label in enumerate(choices, start=1):
                print(f"  {index}. {label}")
            user_input = input("番号を入力してください: ")

            if user_input.isdigit():
                selected = int(user_input) - 1
                if 0 <= selected < len(choices):
                    print()  # 入力後に空行を入れて区切りを付ける。
                    return selected

            print(
                "入力が正しくありません。1 から {0} の番号を選んでください。".format(
                    len(choices)
                )
            )

    def on_game_end(self) -> None:
        """コンソール版では特別な後処理は不要。"""

        print("ゲームを終了します。お疲れさまでした。")


class TkInterface:
    """Tkinter を用いて GUI 上でゲームを遊ぶための実装。"""

    def __init__(self, root: tk.Tk) -> None:  # type: ignore[misc]
        self.root = root
        self.root.title("深夜の洋館からの脱出")

        # Text ウィジェットにゲームの進行ログを表示する。
        self.text = tk.Text(root, width=70, height=24, state="disabled", wrap="word")
        self.text.pack(fill="both", expand=True, padx=12, pady=12)

        # ボタンは別フレームにまとめる。
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(fill="x", padx=12, pady=(0, 12))

        self.choice_var = tk.IntVar(value=-1)
        self.active_buttons: list[tk.Button] = []

        # 初期メッセージ。
        self.display("探索を開始するには、表示される指示に従ってください。")

    def display(self, text: str) -> None:
        """テキストウィジェットに文章を追記する。"""

        self.text.configure(state="normal")
        for paragraph in format_paragraphs(text, width=60):
            self.text.insert("end", paragraph + "\n")
        self.text.insert("end", "\n")
        self.text.see("end")
        self.text.configure(state="disabled")

    def choose(self, question: str, choices: tuple[str, ...]) -> int:
        """ボタンを生成し、押された番号を返す。"""

        self.display(question)
        self._clear_buttons()
        self.choice_var.set(-1)

        for index, label in enumerate(choices):
            button = tk.Button(
                self.button_frame,
                text=f"{index + 1}. {label}",
                command=lambda value=index: self.choice_var.set(value),
                width=35,
                anchor="w",
            )
            button.pack(fill="x", pady=2)
            self.active_buttons.append(button)

        # wait_variable は Tkinter のイベントループをブロックせずに待機できる。
        self.root.wait_variable(self.choice_var)
        self._clear_buttons()
        return int(self.choice_var.get())

    def on_game_end(self) -> None:
        """エンディング後に終了ボタンを表示する。"""

        self._clear_buttons()
        exit_button = tk.Button(
            self.button_frame,
            text="ゲームを閉じる",
            command=self.root.destroy,
            width=35,
        )
        exit_button.pack(pady=4)
        self.active_buttons.append(exit_button)

    def _clear_buttons(self) -> None:
        """既存のボタンを破棄し、次の選択肢に備える。"""

        for button in self.active_buttons:
            button.destroy()
        self.active_buttons.clear()


# =============================
# ゲーム進行のロジック
# =============================

def resolve_room(state: PlayerState, room_name: str, interface: GameInterface) -> None:
    """各部屋で発生するイベントを処理する関数。"""

    interface.display(f"\n--- {room_name} ---")

    # 部屋ごとの演出と選択肢。
    interface.display(
        "壁に染みついた血痕が指し示す方向と、かすかなすすり泣きが聞こえる方向がある。"
    )
    action = interface.choose(
        "どちらへ進みますか？",
        ("血痕を追う", "すすり泣きの元を探る", "祈りを捧げる"),
    )

    # if/elif/else は条件分岐。True になった最初のブロックが実行される。
    if action == 0:
        interface.display("壁に触れると冷たい感触が指を這い、勇気が吸い取られていく……")
        state.courage -= 1
    elif action == 1:
        interface.display("声の正体は同じく迷い込んだ旅人だった。共に脱出の手掛かりを探す。")
        state.clues += 1
    else:
        interface.display("呪文を唱えると、一瞬だけ影が怯んだ。だが代償にあなたの心が削られる。")
        state.courage -= 1
        state.clues += 1

    # 勇気が尽きた場合は、これ以上処理しない。
    if not state.is_alive():
        interface.display("恐怖に心が折れた……。あなたはその場に崩れ落ち、闇が覆い尽くす。")
        return

    # ランダムなノイズ演出。random.choice() で要素を 1 つ選ぶ。
    interface.display(
        random.choice(
            (
                "天井裏を何かが這う音がした。",
                "背後で足音が止まった気がする……振り返る勇気はあるか？",
                "遠くで鈴の音が鳴り、寒気が背筋を走る。",
            )
        )
    )

    # 低確率で追加イベント。
    if random.choice(SUCCESS_TABLE):
        interface.display("偶然見つけた日記に脱出のヒントが記されていた！")
        state.clues += 1
    else:
        interface.display("扉を開けるたびに同じ部屋に戻ってしまう……時間だけが奪われていく。")
        state.courage -= 1

    interface.display(f"現在の勇気: {state.courage} / 集めた手掛かり: {state.clues}")


def reach_finale(state: PlayerState, interface: GameInterface) -> None:
    """ゲームの結末を決定して表示する関数。"""

    interface.display("\n--- 最終局面 ---")

    # 手掛かりが多く残っていれば生還。
    if state.clues >= 3 and state.is_alive():
        interface.display(
            "集めた手掛かりを組み合わせ、あなたは封じられた出口を見つけ出した！\n"
            "夜明けの光が差し込み、館は静かに崩れ落ちていく……あなたは生還した。"
        )
        return

    # ここまで来たが勇気が枯渇した場合はバッドエンド。
    if not state.is_alive():
        interface.display("恐怖に耐え切れず、その場で精神を手放してしまった……。")
        return

    # それ以外はランダムなホラーエンド。
    interface.display(random.choice(FINAL_EVENTS))


def play_game(interface: GameInterface) -> None:
    """共通のゲーム進行関数。インターフェースの種類を問わず利用する。"""

    state = PlayerState()
    interface.display(INTRO_TEXT)

    # for ループで、ROOMS の要素を 1 つずつ処理する。
    for room in ROOMS:
        resolve_room(state, room, interface)
        if not state.is_alive():  # 途中で勇気が尽きたらループを抜ける。
            break

    reach_finale(state, interface)
    interface.on_game_end()


def should_use_gui() -> bool:
    """GUI を起動しても良さそうな環境かどうかを判定する。"""

    if tk is None:
        return False

    # Windows (os.name == "nt") や、DISPLAY / WAYLAND_DISPLAY がある場合は GUI を利用できると判断する。
    return os.name == "nt" or bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def run_gui_game() -> None:
    """Tkinter を用いた GUI 版ゲームを起動する。"""

    if tk is None:  # 保険的なチェック。
        raise RuntimeError("Tkinter が利用できないため GUI を起動できません。")

    root = tk.Tk()
    interface = TkInterface(root)

    # after(0, ...) でイベントループが始まった直後にゲームを実行する。
    root.after(0, lambda: play_game(interface))
    root.mainloop()


def run_console_game() -> None:
    """従来どおりコンソールでゲームを実行する。"""

    play_game(ConsoleInterface())


def main() -> None:
    """ゲーム全体の進行を管理するメイン関数。"""

    if should_use_gui():
        try:
            run_gui_game()
            return
        except Exception as error:
            # GUI の起動に失敗した場合もコンソール版に切り替えて継続する。
            print("GUI の起動に失敗したため、コンソール版に切り替えます。")
            print(f"詳細: {error}\n")

    run_console_game()


if __name__ == "__main__":
    # Python スクリプトとして直接実行されたときだけ main() を呼び出す慣習的な書き方。
    main()
