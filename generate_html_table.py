
"""SHOW rule table."""

import argparse
from pathlib import Path

import ruamel.yaml
from jinja2 import Environment, FileSystemLoader

fstr = {
    "include": "{} {} が 「{}」 のいずれかだ",
    "regex": "{} {} が 「{}」 と一致する",
    "match": "{} {} が 「{}」 と一致する"
}
astr = {
    # word 対象自身
    "word": "対象の単語",
    # parent wordの親
    "parent": "対象の単語の親",
    # semhead wordを含んでいる文節のSEM_HEADであるword
    "semhead": "対象の単語を含んでいる文節の主辞の単語",
    # synhead wordを含んでいる文節のSYN_HEADであるword
    "synhead": "対象の単語を含んでいる文節の機能語の単語",
    # child wordを親とする子単語のリスト (そのうちのひとつが該当すればよい)
    "child": "対象の単語の子である単語",
    # parentchild wordを親とする子単語のリスト (そのうちのひとつが該当すればよい)
    "parentchild": "対象の単語の親の子である単語"
}
tstr = {
    # 文節タイプ: bpos (ex. SEM_HEAD, SYM_HEAD, FUNC, CONT....)
    "bpos": "の 文節タイプ",
    # 日本語（短単位）品詞: xpos (ex. "助詞-格助詞", "接続詞"...)
    "xpos": "の Unidic短単位品詞",
    # 日本語原型: lemma (ex. "だ", "と", "ない", ...)
    "lemma": "の レンマ",
    # upos UD品詞  (ex. ROOT, ADP, ...)
    "upos": "の UD品詞",
    # かかり先の番号  現状0以外使えない
    "depnum": "の 係り先の番号",
    # segment (拡張CabochaのSegment, ex. "Disfluency")
    "segment": "の セグメント",
    # 文末表現 suffixstring (該当のwordの"文節末尾"文字列を確認している ex."Xだ"の"だ")
    "suffixstring": "の 文末表現",
    # 対象語が(格|係|副)助詞かどうか  case (include_child_caseなどでの想定)
    "case": "に 付属する助詞",
    # 対象語の文節タイプ  "体言|用言|コピュラ"   bunsetutype
    "busetutype": "の 文法種類",
    # 指定した距離を表す式X-Y(==|>|<|>=|<=)に合致している
    "disformula": "との 距離",
    # 述語項
    "paslink": "の 述語項",
    # luwpos 日本語長単位品詞
    "luwpos": "の Unidic長単位品詞"
}
POS_RULE = {
    "pos": "短単位品詞",
    "base_lexeme": "原型",
    "luw": "長単位品詞",
    "bpos": "文節タイプ",
    "parent_upos": "単語の親のUPOS"
}
POS_COL = ["短単位品詞", "原型", "長単位品詞", "文節タイプ", "単語の親のUPOS"]
DESEC = """
    <ul>
        <li>対象の単語について条件を満たすものを割り当てる</li>
        <li>上位のものを優先的に割り当てる</li>
        <li>文節タイプ：係り受け情報と文節における位置づけ（主辞や機能語）をラベルづけしたもの</li>
        <ul>
            <li>ROOT: ルート</li>
            <li>SEM_HEAD: 内容語の主辞</li>
            <li>CONT: 主辞ではない内容語</li>
            <li>SYN_HEAD: 機能語の主辞</li>
            <li>FUNC: SYN_HEAD以外の機能語</li>
            <li>NO_HEAD: 上記以外</li>
        </ul>
        <li>文法種類</li>
        <ul>
            <li>文節情報から「体言」「用言」あるいは「コピュラ」かを抽出している</li>
        </ul>
    </ul>
 """


def get_dep_rules_table(dep_yaml_file: str="conf/bccwj_dep_suw_rule.yaml") -> list[list[str]]:
    """Generate DEP rule table as Dataframe."""
    data: list[list[str]] = []
    with Path(dep_yaml_file).open("r", encoding="utf-8") as rdr:
        for rules in ruamel.yaml.YAML().load(rdr.read().replace("\t", "    "))["order_rule"]:
            rrr: list[str] = []
            for rule in rules["rule"]:
                func, iargs = rule
                fff_, aaa, ttt = func.split("_")
                rrr.append(
                    fstr[fff_].format(
                        astr[aaa], tstr[ttt],
                        iargs if not isinstance(iargs, list) else ",".join(iargs)
                    )
                )
            record = ["<ul>" + "".join(f"<li>{r}</li>" for r in rrr) + "</ul>", rules["res"]]
            data.append(record)
    return data


def get_pos_rules_table(pos_yaml_file: str="conf/bccwj_pos_suw_rule.yaml") -> list[list[str]]:
    """Generate POS rule table as Dataframe."""
    data: list[list[str]] = []
    with Path(pos_yaml_file).open("r", encoding="utf-8") as rdr:
        for rule_pair in ruamel.yaml.YAML().load(rdr.read().replace("\t", "    "))["rule"]:
            rule, result = rule_pair
            drule: dict[str, str] = {
                POS_RULE[name]: value for name, value in list(rule.items())
            }
            record = [drule.get(c, "") for c in POS_COL] + [",".join(result)]
            data.append(record)
    return data


def _main() -> None:
    parser = argparse.ArgumentParser(description="変換テーブルのHTML化をする")
    parser.add_argument("pos_yaml_file")
    parser.add_argument("dep_yaml_file")
    parser.add_argument("-t", "--tmpl-folder", default="tmpl/")
    parser.add_argument("-p", "--save-pos-file", default="POS.html")
    parser.add_argument("-d", "--save-dep-file", default="DEPREL.html")
    args = parser.parse_args()

    env = Environment(loader=FileSystemLoader(args.tmpl_folder))
    template = env.get_template("_tmpl.html.j2")
    pdata = get_pos_rules_table(args.pos_yaml_file)
    with Path(args.save_pos_file).open("w", encoding="utf-8") as wrt:
        wrt.write(template.render(
            header=[*POS_COL, "付与UPOS"],
            orders=["id", "suw", "origin", "luw", "btype", "pupos", "upos"],
            record=pdata, desc=DESEC, title="日本語UDにおけるPOS変換規則の一覧"
        ))
    ddata = get_dep_rules_table(args.dep_yaml_file)
    with Path(args.save_dep_file).open("w", encoding="utf-8") as wrt:
        wrt.write(template.render(
            header=["ルール", "付与DEPREL"],
            orders=["id", "rule", "deprel"],
            record=ddata, desc=DESEC, title="日本語UDにおけるDEPREL変換規則の一覧"
        ))


if __name__ == "__main__":
    _main()
