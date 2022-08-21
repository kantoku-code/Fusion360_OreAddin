import adsk.core
import os
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** コマンド識別情報を指定します。 ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_ore'
CMD_NAME = 'Ore Addin Command'
CMD_Description = '俺様の俺様による俺様の為のアドイン'

# コマンドがパネルに昇格することを指定します。
IS_PROMOTED = True

# TODO *** コマンド ボタンを作成する場所を定義します。 ***
# これは、ワークスペース、タブ、パネル、および
# コマンドの横に挿入されます。 配置するコマンドを提供していない
# 最後に挿入します。
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# コマンドアイコンのリソースの場所。ここでは、このディレクトリに「resources」という名前の
# サブフォルダーがあると想定しています。
ICON_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'resources',
    ''
)

# 参照を維持するために使用されるイベント ハンドラーのローカル リスト
# それらは解放されず、ガベージ コレクションも行われません。
local_handlers = []


# ダイアログの二個のSelectionCommandInput
_selIpt1: adsk.core.SelectionCommandInput = None
_selIpt2: adsk.core.SelectionCommandInput = None


# アドイン実行時に実行されます。
def start():
    # コマンド定義を作成します。
    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID,
        CMD_NAME,
        CMD_Description,
        ICON_FOLDER
    )

    # コマンド作成イベントのイベント ハンドラーを定義します。
    # ボタンがクリックされたときに呼び出されます。
    futil.add_handler(
        cmd_def.commandCreated,
        command_created
    )

    # ******** UI にボタンを追加して、ユーザーがコマンドを実行できるようにします。 ********
     # ボタンが作成されるターゲット ワークスペースを取得します。
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # ボタンが作成されるパネルを取得します。
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # UI で、指定された既存のコマンドの後にボタン コマンド コントロールを作成します。
    control = panel.controls.addCommand(
        cmd_def,
        COMMAND_BESIDE_ID,
        False
    )

    # コマンドがメイン ツールバーに昇格するかどうかを指定します。
    control.isPromoted = IS_PROMOTED


# アドイン停止時に実行。
def stop():
    # このコマンドのさまざまな UI 要素を取得します
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # ボタンコマンドコントロールを削除
    if command_control:
        command_control.deleteMe()

    # コマンド定義を削除
    if command_definition:
        command_definition.deleteMe()


# ユーザーが UI の対応するボタンをクリックしたときに呼び出される関数。
# これは、コマンド ダイアログの内容を定義し、コマンド関連のイベントに接続します。
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    inputs = args.command.commandInputs

    global _selIpt1, _selIpt2
    _selIpt1 = inputs.addSelectionInput(
        'selIpt1',
        '1点目を選択',
        'スケッチの点を選択して下さい'
    )
    _selIpt1.addSelectionFilter('SketchPoints')
    _selIpt1.setSelectionLimits(0)

    _selIpt2 = inputs.addSelectionInput(
        'selIpt2',
        '2点目を選択',
        'スケッチの点を選択して下さい'
    )
    _selIpt2.addSelectionFilter('SketchPoints')
    _selIpt2.setSelectionLimits(0)

    # TODO このコマンドで必要なイベントに接続します。
    futil.add_handler(
        args.command.execute,
        command_execute,
        local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.inputChanged,
        command_input_changed,
        local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.executePreview,
        command_preview,
        local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.validateInputs,
        command_validate_input,
        local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.preSelect,
        command_preSelect,
        local_handlers=local_handlers
    )
    futil.add_handler(
        args.command.destroy,
        command_destroy,
        local_handlers=local_handlers
    )


# このイベント ハンドラーは、マウスカーソルが選択対象上にある時に発生します。
# 複雑な条件の選択フィルターとして利用しています。
def command_preSelect(args: adsk.core.CommandEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    # イベントが発生したSelectionCommandInput
    selIpt: adsk.core.SelectionCommandInput = args.activeInput

    # 既に選択済みなら、選択させない
    if selIpt.selectionCount > 0:
        args.isSelectable = False


# このイベント ハンドラーは、ユーザーがコマンド ダイアログの [OK] ボタンをクリックしたとき、または
# コマンド入力ではなく、作成されたイベントがダイアログに対して作成された直後に呼び出されます。
def command_execute(args: adsk.core.CommandEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    # ダイアログ上のSelectionCommandInput
    global _selIpt1, _selIpt2

    # 選択された点で一時的なBRepBody(球体)作成
    body: adsk.fusion.BRepBody = createSphereBetweenTwoPoints(
        _selIpt1.selection(0).entity,
        _selIpt2.selection(0).entity,
    )

    # 実体化
    createBody(body)


# このイベント ハンドラは、コマンドがグラフィックス ウィンドウで新しいプレビューを
# 計算する必要があるときに呼び出されます。
def command_preview(args: adsk.core.CommandEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    # ダイアログ上のSelectionCommandInput
    global _selIpt1, _selIpt2

    # 選択された点で一時的なBRepBody(球体)作成
    body: adsk.fusion.BRepBody = createSphereBetweenTwoPoints(
        _selIpt1.selection(0).entity,
        _selIpt2.selection(0).entity,
    )

    # 球体作成に失敗した際はOKボタンを押させない
    if not body:
        args.isValidResult = True
        return

    # 球体を標示
    showPreviewBody(body)


# このイベント ハンドラーは、ユーザーがコマンド ダイアログで何かを変更したときに呼び出されます
# その変更に基づいて他の入力の値を変更できるようにします。
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name} - {args.input.id}')

    # 今回はadsk.core.SelectionCommandInputの変更以外は
    # 受け付けない事にしています。
    if args.input.classType() != adsk.core.SelectionCommandInput.classType():
        return

    # ダイアログ上のSelectionCommandInput
    global _selIpt1, _selIpt2

    # 一個目が未選択ならフォーカス
    if _selIpt1.selectionCount < 1:
        _selIpt1.hasFocus = True
        return

    # 二個目が未選択ならフォーカス
    if _selIpt2.selectionCount < 1:
        _selIpt2.hasFocus = True


# このイベント ハンドラーは、ユーザーがダイアログ内のいずれかの入力を操作したときに呼び出されます
# すべての入力が有効であることを確認し、[OK] ボタンを有効にすることができます。
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    # ダイアログ上のSelectionCommandInput
    global _selIpt1, _selIpt2

    # それぞれSelectionCommandInputが未選択時はFalse
    if _selIpt1.selectionCount < 1 or _selIpt2.selectionCount < 1:
        args.areInputsValid = False
        return

    # 選択された点で球体作成
    res = createSphereBetweenTwoPoints(
        _selIpt1.selection(0).entity,
        _selIpt2.selection(0).entity,
    )

    # 球体作成に失敗した際はOKボタンを押させない
    if not res:
        args.areInputsValid = False


# このイベント ハンドラは、コマンドの終了時に呼び出されます。
def command_destroy(args: adsk.core.CommandEventArgs):
    # デバッグ用の一般的なログ。
    futil.log(f'{CMD_NAME} {args.firingEvent.name}')

    global local_handlers
    local_handlers = []


# 2点間を直径とする球体の一時的なBRepBody作成
def createSphereBetweenTwoPoints(
    sktPnt1: adsk.fusion.SketchPoint,
    sktPnt2: adsk.fusion.SketchPoint) -> adsk.fusion.BRepBody:

    # ジオメトリの取得
    pnt1: adsk.core.Point3D = sktPnt1.worldGeometry
    pnt2: adsk.core.Point3D = sktPnt2.worldGeometry

    # 半径の取得
    radius: float = pnt1.distanceTo(pnt2) * 0.5
    if not radius > 0:
        return False # 同一点の場合はFalseとし処理中止

    # 中間点の取得
    centerPnt: adsk.core.Point3D = adsk.core.Point3D.create(
        (pnt1.x + pnt2.x) * 0.5,
        (pnt1.y + pnt2.y) * 0.5,
        (pnt1.z + pnt2.z) * 0.5,
    )

    # 球体作成
    tmpMgr: adsk.fusion.TemporaryBRepManager = adsk.fusion.TemporaryBRepManager.get()
    sphere: adsk.fusion.BRepBody = tmpMgr.createSphere(centerPnt, radius)

    return sphere


# 一時的なBRepBodyをカスタムグラフィックスで表示させる
def showPreviewBody(
    body: adsk.fusion.BRepBody):

    # root 取得
    app: adsk.core.Application = adsk.core.Application.get()
    des: adsk.fusion.Design = app.activeProduct
    root: adsk.fusion.Component = des.rootComponent

    # カスタムグラフィックスで表示させる
    cgGroup: adsk.fusion.CustomGraphicsGroup = root.customGraphicsGroups.add()
    cgBody:adsk.fusion.CustomGraphicsBRepBody = cgGroup.addBRepBody(body)

    # 色の設定　いい加減です・・・。
    cgBody.color = adsk.fusion.CustomGraphicsBasicMaterialColorEffect.create(
        adsk.core.Color.create(0, 255, 0,255),
        adsk.core.Color.create(255, 255, 0, 255),
        adsk.core.Color.create(0, 0, 255, 255),
        adsk.core.Color.create(0, 0, 0, 255),
        10,
        0.5
    )


# 一時的なBRepBodyを実体化
def createBody(
    body: adsk.fusion.BRepBody):

    app: adsk.core.Application = adsk.core.Application.get()
    des: adsk.fusion.Design = app.activeProduct
    root: adsk.fusion.Component = des.rootComponent

    isParametric: bool = True
    if des.designType == adsk.fusion.DesignTypes.DirectDesignType:
        isParametric = False

    occ: adsk.fusion.Occurrence = root.occurrences.addNewComponent(
        adsk.core.Matrix3D.create()
    )

    comp: adsk.fusion.Component = occ.component

    baseFeat: adsk.fusion.BaseFeature = None
    if isParametric:
        baseFeat = comp.features.baseFeatures.add()

    bodies: adsk.fusion.BRepBodies = comp.bRepBodies

    if isParametric:
        baseFeat.startEdit()
        bodies.add(body, baseFeat)
        baseFeat.finishEdit()
    else:
        bodies.add(body)