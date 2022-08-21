# ここで、アドインに追加されるコマンドを定義します。

# TODO 作成したコマンドに対応するモジュールをインポートします。
# コマンドを追加する場合は、既存のディレクトリの 1 つを複製し、ここにインポートします。
# 「entry」という名前のデフォルトモジュールがあると仮定して、
# エイリアスを使用する必要があります (「entry」を「my_module」としてインポート)。
from .Ore import entry as ore

# TODO インポートしたモジュールをこのリストに追加します。
# Fusion は自動的に start() および stop() 関数を呼び出します。
commands = [
    ore,
]


# 各モジュールで「start」関数を定義したと仮定します。
# アドインの起動時にstart関数が実行されます。
def start():
    for command in commands:
        command.start()


# 各モジュールで「stop」関数を定義したと仮定します。
# アドインが停止するとstop関数が実行されます。
def stop():
    for command in commands:
        command.stop()