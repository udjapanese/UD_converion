# -*- coding: utf-8 -*-

"""
SHOW rule table
"""

import ruamel.yaml
import pandas
import argparse

from jinja2 import Template

fstr = {
    "include": "{} {} が 「{}」 のいずれかだ",
    "regex": "{} {} が 「{}」 と一致する",
    "match": "{} {} が 「{}」 と一致する"
}
astr = {
    # word: 対象自身
    "word": "対象の単語",
    # parent: wordの親
    "parent": "対象の単語の親",
    # semhead: wordを含んでいる文節のSEM_HEADであるword
    "semhead": "対象の単語を含んでいる文節の主辞の単語",
    # synhead: wordを含んでいる文節のSYN_HEADであるword
    "synhead": "対象の単語を含んでいる文節の機能語の単語",
    # child: wordを親とする子単語のリスト（そのうちのひとつが該当すればよい）
    "child": "対象の単語の子である単語",
    # parentchild: wordを親とする子単語のリスト（そのうちのひとつが該当すればよい）
    "parentchild": "対象の単語の親の子である単語"
}
tstr = {
    # 文節タイプ: bpos (ex. SEM_HEAD, SYM_HEAD, FUNC, CONT....)
    "bpos": "の 文節タイプ",
    # 日本語（短単位）品詞: xpos (ex. "助詞-格助詞", "接続詞"...)
    "xpos": "の Unidic短単位品詞",
    # 日本語原型: lemma (ex. "だ", "と", "ない", ...)
    "lemma": "の レンマ",
    # UD品詞: upos (ex. ROOT, ADP, ...)
    "upos": "の UD品詞",
    # かかり先の番号 (現状0以外使えない)
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
    # 日本語長単位品詞: luwpos
    "luwpos": "の Unidic長単位品詞"
}
POS_RULE = {
    "pos": "短単位品詞",
    "base_lexeme": "原型",
    "luw": "長単位品詞",
    "bpos": "単語の親のUPOS",
    "parent_upos": "単語の親のUPOS"
}
POS_COL = ["短単位品詞", "原型", "長単位品詞", "単語の親のUPOS", "単語の親のUPOS"]
DESEC = """
            <ul>
                <li>対象の単語について条件を満たすものを割り当てる</li>
                <li>上位のものを優先的に割り当てる</li>
                <li>文節タイプ</li>
                <ul>
                    <li>係り受け情報と文節における位置づけ（主辞や機能語）をラベルづけしたもの</li>
                </ul>
                <li>文法種類</li>
                <ul>
                    <li>文節情報から「体言」「用言」あるいは「コピュラ」かを抽出している</li>
                </ul>
            </ul>
 """

def get_dep_rules_table(dep_yaml_file: str="conf/bccwj_dep_suw_rule.yaml") -> pandas.DataFrame:
    data: list[list[str]] = []
    yaml = ruamel.yaml.YAML()
    rule_set = yaml.load(open(dep_yaml_file, "r").read().replace('\t', '    '))
    for rules in rule_set["order_rule"]:
        rrr: list[str] = []
        for rule in rules["rule"]:
            func, iargs = rule
            f, a, t = func.split("_")
            fff = fstr[f]
            rrr.append(fff.format(astr[a], tstr[t], iargs if not isinstance(iargs, list) else ",".join(iargs)))
        data.append(["<ul>" + "".join(["<li>"+r+"</li>" for r in rrr]) + "</ul>", rules["res"]])
    df = pandas.DataFrame(data, columns=["ルール", "付与DEPREL"])
    df.index = df.index + 1
    return df


def get_pos_rules_table(pos_yaml_file: str="conf/bccwj_pos_suw_rule.yaml") -> pandas.DataFrame:
    data: list[list[str]] = []
    yaml = ruamel.yaml.YAML()
    rule_set = yaml.load(open(pos_yaml_file, "r").read().replace('\t', '    '))
    for rule_pair in rule_set["rule"]:
        rule, result = rule_pair
        drule: dict[str, str] = {}
        for name, value in list(rule.items()):
            drule[POS_RULE[name]] = value
        data.append([drule[c] if c in drule else "" for c in POS_COL] + [result[0]])
    df = pandas.DataFrame(data, columns=POS_COL + ["付与UPOS"])
    df.index = df.index + 1
    return df


def _main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("pos_yaml_file")
    parser.add_argument("dep_yaml_file")
    parser.add_argument("-t", "--tmpl-file", default="tmpl/_tmpl.html")
    parser.add_argument("-p", "--save-pos-file", default="POS.html")
    parser.add_argument("-d", "--save-dep-file", default="DEP.html")
    args = parser.parse_args()

    pos_template = Template(open(args.tmpl_file, "r").read())
    pos_df = get_pos_rules_table(args.pos_yaml_file)
    pdata = pos_df.to_html(justify="unset", classes="pure-table pure-table-bordered", index_names=True, escape=False, index=True)
    with open(args.save_pos_file, "w") as wrt:
        wrt.write(pos_template.render(table=pdata, desc=DESEC, title="日本語UDにおけるPOS変換規則の一覧"))
    dep_template = Template(open(args.tmpl_file, "r").read())
    dep_df = get_dep_rules_table(args.dep_yaml_file)
    ddata = dep_df.to_html(justify="unset", classes="pure-table pure-table-bordered", index_names=True, escape=False, index=True)
    with open(args.save_dep_file, "w") as wrt:
        wrt.write(dep_template.render(table=ddata, desc=DESEC, title="日本語UDにおけるDEPREL変換規則の一覧"))


if __name__ == '__main__':
    _main()
