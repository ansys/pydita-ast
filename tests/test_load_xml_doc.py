import ansys.dita.ast.load_xml_doc as lxd


def test_load_links(link_path):
    links = lxd.load_links(link_path)
    assert links["ds_Support_Types"] == (
        "wb_sim",
        "",
        "ds_Elastic_Support.html",
        "Support Type Boundary Conditions",
    )


def test_load_fcache(graph_path):
    fcache = lxd.load_fcache(graph_path)
    assert fcache["gcmdrsymm4"] == "gcmdrsymm4.png"


def test_load_docu_global(term_path):
    docu_global = lxd.load_docu_global(term_path)
    assert docu_global["acpmdug"] == ("acp_md", "acp_md", "bk_acp_md")


def test_load_terms(load_terms):
    terms, version_variables = load_terms
    assert terms["me"] == "Ansys Mechanical"
    assert version_variables.autogenerated_directory_name == "ansys.dita.generatedcommands"
    assert version_variables.version == terms["ansys_internal_version"]
