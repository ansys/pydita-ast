.. graphviz::
    :caption: Predefined XML directory format
    :alt: Predefined XML directory format
    :align: center

      digraph "sphinx-ext-graphviz" {
         size="8,6";
         rankdir="LR";
         bgcolor="white";
         graph [
           fontname="Verdana", fontsize="10", color="black", fillcolor="white", splines=ortho, nodesep=0.2
         ];
         node [
           fontname="Verdana", fontsize="10", style="filled", color="black", fillcolor="#ffc107", shape="rarrow"
         ];
         edge[
          arrowsize="0.5"
         ]

         XML_directory [
           label="XML_documentation", shape="folder"
         ];

         terms [
           label="terms", shape="folder"
         ];

         character_directory [
           label="ent", shape="folder"
         ];

         cd_ent_files [
           label=".ent files", shape="file"
         ];

         glb [
           label="glb", shape="folder"
         ];

         manual_file [
           label="manuals.ent", shape="file"
         ];
        
         global_terms_file [
           label="terms_global.ent", shape="file"
         ];

         variable_file [
           label="build_variables.ent", shape="file"
         ];

         graphics [
           label="graphics", shape="folder"
         ];

         gifs [
           label="gifs", shape="file"
         ];

         images [
           label="images", shape="file"
         ];

         links [
           label="links", shape="folder"
         ];

         db_files [
           label=".db files", shape="file"
         ];

         xml [
           label="xml", shape="folder"
         ];

         subdirectorys [
           label="subdirectorys", shape="folder"
         ];

         mathgraphics_directory [
           label="mathgraphics_directory", shape="folder"
         ];

         svg_files [
           label=".svg files", shape="file"
         ];

         sub_xml_files[
           label=".xml files", shape="file"
         ];

         xml_xml_files [
           label=".xml files", shape="file"
         ];

         xml_ent_files [
           label=".ent files", shape="file"
         ];


      XML_directory -> terms
      XML_directory -> graphics
      XML_directory -> links
      XML_directory -> xml

      terms -> character_directory

      character_directory -> cd_ent_files

      terms -> glb
      
      glb -> manual_file
      glb -> global_terms_file
      glb -> variable_file

      graphics -> gifs
      graphics -> images

      links -> db_files

      xml -> subdirectorys
      xml -> xml_xml_files
      xml -> xml_ent_files

      subdirectorys -> mathgraphics_directory
      mathgraphics_directory -> svg_files

      subdirectorys -> sub_xml_files

     }



