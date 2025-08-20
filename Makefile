get-structure-creator:
	curl -O https://raw.githubusercontent.com/kolelan/create_structure/main/create_structure.py

create-structure:
	python3 create_structure.py
	
structure: get-structure-creator create-structure


