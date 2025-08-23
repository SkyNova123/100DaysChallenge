
# game.py — Pygame Zero (pgzrun game.py)
# ゲーム画面サイズ
WIDTH, HEIGHT = 480, 720
# プレイヤーのサイズ（幅、高さ）
PLAYER_W, PLAYER_H = 60, 16
# 星の半径
STAR_R = 12

import random, time
# プレイヤーの初期位置（画面中央）
player_x = WIDTH // 2
# スコア
score = 0
# ゲーム開始時刻
start_time = time.time()
# ゲーム時間（秒）
GAME_TIME = 30.0
# ゲーム終了フラグ
game_over = False

class Star:
    """落ちてくる星のクラス"""
    def __init__(self): self.reset()
    
    def reset(self):
        """星の位置と速度を初期化"""
        # 画面上端の左右端を避けてランダムに配置
        self.x = random.randint(STAR_R, WIDTH - STAR_R)
        # 画面上端より少し上から開始
        self.y = -STAR_R
        # 落下速度をランダムに設定（180-320ピクセル/秒）
        self.v = random.uniform(180, 320)
    
    def update(self, dt):
        """星の位置を更新"""
        # 落下速度に応じて位置を更新
        self.y += self.v * dt
        # 画面下端を過ぎたらリセット
        if self.y - STAR_R > HEIGHT: self.reset()

# 5個の星を生成
stars = [Star() for _ in range(5)]

def intersects(px, py, pw, ph, cx, cy, cr):
    """矩形と円の当たり判定を行う関数
    
    Args:
        px, py: 矩形の左上座標
        pw, ph: 矩形の幅と高さ
        cx, cy: 円の中心座標
        cr: 円の半径
    
    Returns:
        bool: 当たっている場合True
    """
    # 円の中心から矩形への最短距離の点を求める
    nx = max(px, min(cx, px + pw))
    ny = max(py, min(cy, py + ph))
    # 円の中心からその点までの距離を計算
    dx, dy = cx - nx, cy - ny
    # 距離が円の半径以下なら当たり
    return (dx*dx + dy*dy) <= cr*cr

def on_key_down(key):
    """キーが押された時の処理"""
    global game_over
    # ゲーム終了時にスペースキーが押されたらリスタート
    if game_over and key.name == "SPACE": reset_game()

def update(dt):
    """ゲームの状態を更新する関数（毎フレーム呼ばれる）"""
    global player_x, score, game_over
    # ゲーム終了時は更新しない
    if game_over: return
    
    # プレイヤーの移動処理
    if keyboard.left:  player_x -= 300 * dt  # 左矢印キー：左に移動
    if keyboard.right: player_x += 300 * dt  # 右矢印キー：右に移動
    # プレイヤーを画面内に制限
    player_x = max(0, min(player_x, WIDTH - PLAYER_W))
    
    # プレイヤーのY座標（固定）
    py = HEIGHT - 80
    
    # 全ての星を更新し、当たり判定を行う
    for s in stars:
        s.update(dt)
        # プレイヤーと星の当たり判定
        if intersects(player_x, py, PLAYER_W, PLAYER_H, s.x, s.y, STAR_R):
            score += 1  # スコア加算
            s.reset()   # 星をリセット
    
    # 制限時間チェック
    if time.time() - start_time >= GAME_TIME: 
        game_over = True

def draw():
    """画面を描画する関数（毎フレーム呼ばれる）"""
    # 背景を暗いグレーで塗りつぶし
    screen.fill((18, 18, 22))
    
    # プレイヤーの描画
    py = HEIGHT - 80  # プレイヤーのY座標
    screen.draw.filled_rect(Rect((player_x, py), (PLAYER_W, PLAYER_H)), (230, 120, 60))
    
    # 星の描画
    for s in stars: 
        screen.draw.filled_circle((s.x, s.y), STAR_R, (255, 230, 100))
    
    # 残り時間の計算
    elapsed = min(time.time() - start_time, GAME_TIME)
    remain = max(0.0, GAME_TIME - elapsed)
    
    # UI表示
    screen.draw.text(f"Score: {score}", (10, 10), fontsize=32, color="white")
    screen.draw.text(f"Time : {remain:04.1f}s", (10, 44), fontsize=28, color="white")
    
    # ゲームオーバー時の表示
    if game_over:
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2-20), fontsize=64,
                         color="white", owidth=1, ocolor="black")
        screen.draw.text(f"Final Score: {score}", center=(WIDTH//2, HEIGHT//2+40),
                         fontsize=36, color="white")
        screen.draw.text("Press SPACE to retry", center=(WIDTH//2, HEIGHT//2+90),
                         fontsize=28, color="white")

def reset_game():
    """ゲームをリセットして新しくゲームを開始する"""
    global score, start_time, game_over
    # スコアをリセット
    score = 0
    # 全ての星を初期位置に戻す
    for s in stars: s.reset()
    # 開始時間を現在時刻に設定
    start_time = time.time()
    # ゲーム終了フラグをオフ
    game_over = False
