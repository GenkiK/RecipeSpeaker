import re


#
# ルールベースの言語理解を行うクラス
#
class SluRule:

    # 意味・格フレーム
    frames = []

    # 初期化
    def __init__(self, num_proc):
        self.num_proc = num_proc
        self.def_frame()

    # 格フレームを定義
    def def_frame(self):

        from_top = "(最初から|初めから|始めから|一から|1から|最初に戻)"
        # go_back = "戻って"
        first_proc = "(最初|初め|始め|まず)"
        next_proc = "次"
        repeat = "(もう1度|もう一度|再度|もう1回|もう一回|もっかい|なんて|何て)"  # proc_noよりもこちらを優先的に見るようにする(中に"1"というのが両方に含まれているから)
        # last_proc = "最後"
        prev_proc = "(前|戻)"
        proc_no = "(" + "|".join([f"{i}つ目|{i}番" for i in range(1, self.num_proc + 1)]) + ")"
        end = "(終わり|おわり|終了|もういいよ)"

        # 格フレームの意味と対応させる
        # ここにユーザ意図の種類を記述しておくことも可能
        self.frames = [
            ["from the top", from_top],
            ["first procedure", first_proc],
            ["next procedure", next_proc],
            ["repeat", repeat],
            # ["last procedure", last_proc],
            ["previous procedure", prev_proc],
            ["No. of procedure", proc_no],
            ["end", end],
        ]

    # 入力文に対して意味・格フレームを用いてパージングする
    # 戻り値は，マッチしたスロット名とスロット値のリスト
    def parse_frame(self, input_sentence):
        # 先に定義したフレームで見つかったら，それ以降のフレームは探索しないようにする(フレームが重複するのを回避)
        for frame in self.frames:
            result = re.search(frame[1], input_sentence)
            if result is not None:
                # マッチしたスロット名，スロット値を取得・格納
                intent = None
                slot_name = frame[0]
                slot_value = result.group()
                return {"intent": intent, "slot_name": slot_name, "slot_value": slot_value}
        return {"intent": None, "slot_name": "unknown", "slot_value": None}


if __name__ == "__main__":

    # 入力データを読み込む

    with open("./data/slu-sample1.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()

    list_input_data = []
    for line in lines:
        if not line.strip():
            continue
        list_input_data.append(line.strip())

    parser = SluRule()

    # 入力文をマッチさせてみる
    for data in list_input_data:

        # 意味・格フレーム
        results = parser.parse_frame(data)
        print("[Semantic/Case frame]")
        for r in results:
            print(r["slot_name"] + " : " + r["slot_value"])
        if len(results) == 0:
            print("Nothing was matched")
        print()
