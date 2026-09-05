-- seeds/default.sql

-- 1. System Stats (Total Canonical Entities: 50)
INSERT OR REPLACE INTO system_stats (id, total_entities) VALUES (1, 50);

-- 2. Canonical Entities (50 Total: Seed 1 + Seed 2 + Seed 3)
INSERT INTO entities (id, canonical_form, entity_type, primary_metaphone, secondary_metaphone) VALUES 
-- Core Infrastructure & Tools (Seed 1 & 2)
('neovim', 'Neovim', 'TECH_TERM', 'NFM', 'NFM'),
('void', 'Void', 'TECH_TERM', 'FT', 'FT'),
('void_linux', 'Void Linux', 'TECH_TERM', 'FTLNKS', 'FTLNKS'),
('zsh', 'Zsh', 'TECH_TERM', 'SX', 'SX'),
('tmux', 'Tmux', 'TECH_TERM', 'TMKS', 'TMKS'),
('docker', 'Docker', 'TECH_TERM', 'TKR', 'TKR'),
('kubernetes', 'Kubernetes', 'TECH_TERM', 'KPRNTS', 'KPRNTS'),
('nginx', 'Nginx', 'TECH_TERM', 'NJNKS', 'NKNKS'),

-- Databases, ORMs & Data Science (Seed 1 & 2)
('redis', 'Redis', 'TECH_TERM', 'RTS', 'RTS'),
('postgresql', 'PostgreSQL', 'TECH_TERM', 'PSTKRSKL', 'PSTKRSKL'),
('dynamodb', 'DynamoDB', 'TECH_TERM', 'TNMTP', 'TNMTP'),
('diesel', 'Diesel', 'TECH_TERM', 'TSL', 'TSL'),
('sqlalchemy', 'SQLAlchemy', 'TECH_TERM', 'SKLLXM', 'SKLLKM'),
('pandas', 'Pandas', 'TECH_TERM', 'PNTS', 'PNTS'),
('conda', 'Conda', 'TECH_TERM', 'KNT', 'KNT'),
('jupyter', 'Jupyter', 'TECH_TERM', 'JPTR', 'APTR'),

-- Frameworks, APIs & Services (Seed 1 & 2)
('fastapi', 'FastAPI', 'TECH_TERM', 'FSTP', 'FSTP'),
('celery', 'Celery', 'TECH_TERM', 'SLR', 'SLR'),
('postman', 'Postman', 'TECH_TERM', 'PSTMN', 'PSTMN'),
('json', 'JSON', 'TECH_TERM', 'JSN', 'ASN'),
('cognito', 'Cognito', 'TECH_TERM', 'KNT', 'KKNT'),
('kivi', 'Kivi', 'TECH_TERM', 'KF', 'KF'),

-- Organizations & People (Seed 1 & 2)
('aaditya', 'Aaditya', 'PERSON', 'ATT', 'ATT'),
('atomberg', 'Atomberg', 'ORG', 'ATMPRK', 'ATMPRK'),
('iitm', 'IITM', 'ORG', 'ATM', 'ATM'),

-- Gaming (Seed 1)
('efootball', 'eFootball', 'GAME', 'AFTPL', 'AFTPL'),
('clash_royale', 'Clash Royale', 'GAME', 'KLXRL', 'KLXRL'),
('sable', 'Sable', 'GAME', 'SPL', 'SPL'),

-- 22 New Entities (Seed 3)
('grafana', 'Grafana', 'TECH_TERM', 'KRFN', 'KRFN'),
('prometheus', 'Prometheus', 'TECH_TERM', 'PRM0S', 'PRMTS'),
('kafka', 'Kafka', 'TECH_TERM', 'KFK', 'KFK'),
('pycharm', 'PyCharm', 'TECH_TERM', 'PXRM', 'PKRM'),
('wezterm', 'WezTerm', 'TECH_TERM', 'ASTRM', 'FTSTRM'),
('alacritty', 'Alacritty', 'TECH_TERM', 'ALKRT', 'ALKRT'),
('ansible', 'Ansible', 'TECH_TERM', 'ANSPL', 'ANSPL'),
('terraform', 'Terraform', 'TECH_TERM', 'TRFRM', 'TRFRM'),
('rust', 'Rust', 'TECH_TERM', 'RST', 'RST'),
('golang', 'Golang', 'TECH_TERM', 'KLNK', 'KLNK'),
('grpc', 'gRPC', 'TECH_TERM', 'KRPK', 'KRPK'),
('graphql', 'GraphQL', 'TECH_TERM', 'KRFKL', 'KRFKL'),
('supabase', 'Supabase', 'TECH_TERM', 'SPPS', 'SPPS'),
('cloudflare', 'Cloudflare', 'TECH_TERM', 'KLTFLR', 'KLTFLR'),
('arch_linux', 'Arch Linux', 'TECH_TERM', 'ARXLNKS', 'ARKLNKS'),
('picom', 'Picom', 'TECH_TERM', 'PKM', 'PKM'),
('valheim', 'Valheim', 'GAME', 'FLM', 'FLM'),
('max_payne', 'Max Payne', 'GAME', 'MKSPN', 'MKSPN'),
('savar', 'Savar', 'PERSON', 'SFR', 'SFR'),
('saurabh', 'Saurabh', 'PERSON', 'SRP', 'SRP'),
('pydantic', 'Pydantic', 'TECH_TERM', 'PTNTK', 'PTNTK'),
('certbot', 'Certbot', 'TECH_TERM', 'SRTPT', 'SRTPT');

-- 3. Phonetic Aliases
INSERT INTO phonetic_aliases (id, entity_id, alias, primary_metaphone, secondary_metaphone) VALUES 
-- Existing Aliases
('aaditya_aditya', 'aaditya', 'aditya', 'ATT', 'ATT'),
('atomberg_adam_berg', 'atomberg', 'adam berg', 'ATMPRK', 'ATMPRK'),
('atomberg_atom_berg', 'atomberg', 'atom berg', 'ATMPRK', 'ATMPRK'),
('iitm_item', 'iitm', 'item', 'ATM', 'ATM'),
('json_jason', 'json', 'jason', 'JSN', 'ASN'),
('kivi_keevee', 'kivi', 'keevee', 'KF', 'KF'),
('cognito_incognito', 'cognito', 'incognito', 'ANKNT', 'ANKKNT'),
('void_avoid', 'void', 'avoid', 'AFT', 'AFT'),
('void_linux_boyd_linux', 'void_linux', 'boyd linux', 'PTLNKS', 'PTLNKS'),
('neovim_neo_them', 'neovim', 'neo them', 'N0M', 'NTM'),
('redis_read_is', 'redis', 'read is', 'RTS', 'RTS'),
('fastapi_fast_api', 'fastapi', 'fast api', 'FSTP', 'FSTP'),
('diesel_dezel', 'diesel', 'dezel', 'TSL', 'TSL'),
('pandas_pan_das', 'pandas', 'pan das', 'PNTS', 'PNTS'),
('conda_corner', 'conda', 'corner', 'KRNR', 'KRNR'),
('zsh_z_shell', 'zsh', 'z shell', 'SXL', 'SXL'),
('tmux_tea_max', 'tmux', 'tea max', 'TMKS', 'TMKS'),
('jupyter_jewel_iter', 'jupyter', 'jewel iter', 'JLTR', 'ALTR'),
('postman_post_man', 'postman', 'post man', 'PSTMN', 'PSTMN'),
('docker_dock_her', 'docker', 'dock her', 'TKR', 'TKR'),
('kubernetes_cube_are_net_is', 'kubernetes', 'cube are net is', 'KPRNTS', 'KPRNTS'),
('nginx_engine_x', 'nginx', 'engine x', 'ANJNKS', 'ANKNKS'),
('celery_salary', 'celery', 'salary', 'SLR', 'SLR'),
('efootball_ea_football', 'efootball', 'ea football', 'AFTPL', 'AFTPL'),

-- 22 New Aliases (Seed 3)
('grafana_gruff_on_a', 'grafana', 'gruff on a', 'KRFN', 'KRFN'),
('grafana_graft_on_a', 'grafana', 'graft on a', 'KRFTN', 'KRFTN'),
('prometheus_pro_me_the_us', 'prometheus', 'pro me the us', 'PRM0S', 'PRMTS'),
('prometheus_per_me_the_us', 'prometheus', 'per me the us', 'PRM0S', 'PRMTS'),
('kafka_cough_car', 'kafka', 'cough car', 'KFKR', 'KFKR'),
('kafka_calf_car', 'kafka', 'calf car', 'KLFKR', 'KLFKR'),
('pycharm_pie_charm', 'pycharm', 'pie charm', 'PXRM', 'PKRM'),
('wezterm_west_term', 'wezterm', 'west term', 'ASTTRM', 'FSTTRM'),
('wezterm_wes_term', 'wezterm', 'wes term', 'ASTRM', 'FSTRM'),
('alacritty_a_lack_pretty', 'alacritty', 'a lack pretty', 'ALKPRT', 'ALKPRT'),
('alacritty_alacrity', 'alacritty', 'alacrity', 'ALKRT', 'ALKRT'),
('ansible_and_civil', 'ansible', 'and civil', 'ANTSFL', 'ANTSFL'),
('ansible_an_civil', 'ansible', 'an civil', 'ANSFL', 'ANSFL'),
('terraform_terra_form', 'terraform', 'terra form', 'TRFRM', 'TRFRM'),
('terraform_terror_form', 'terraform', 'terror form', 'TRRFRM', 'TRRFRM'),
('rust_roast', 'rust', 'roast', 'RST', 'RST'),
('golang_go_lang', 'golang', 'go lang', 'KLNK', 'KLNK'),
('grpc_gee_are_pee_see', 'grpc', 'gee are pee see', 'JRPS', 'KRPS'),
('graphql_graph_ql', 'graphql', 'graph ql', 'KRFKL', 'KRFKL'),
('supabase_super_base', 'supabase', 'super base', 'SPRPS', 'SPRPS'),
('supabase_soup_a_base', 'supabase', 'soup a base', 'SPPS', 'SPPS'),
('cloudflare_cloud_flare', 'cloudflare', 'cloud flare', 'KLTFLR', 'KLTFLR'),
('arch_linux_art_linux', 'arch_linux', 'art linux', 'ARTLNKS', 'ARTLNKS'),
('picom_pie_com', 'picom', 'pie com', 'PKM', 'PKM'),
('picom_pick_om', 'picom', 'pick om', 'PKM', 'PKM'),
('valheim_val_hime', 'valheim', 'val hime', 'FLM', 'FLM'),
('valheim_well_him', 'valheim', 'well him', 'ALM', 'FLM'),
('max_payne_max_pain', 'max_payne', 'max pain', 'MKSPN', 'MKSPN'),
('savar_sever', 'savar', 'sever', 'SFR', 'SFR'),
('savar_server', 'savar', 'server', 'SRFR', 'SRFR'),
('saurabh_sourav', 'saurabh', 'sourav', 'SRF', 'SRF'),
('saurabh_saurav', 'saurabh', 'saurav', 'SRF', 'SRF'),
('pydantic_pie_dantick', 'pydantic', 'pie dantick', 'PTNTK', 'PTNTK'),
('pydantic_pedantic', 'pydantic', 'pedantic', 'PTNTK', 'PTNTK'),
('certbot_search_bot', 'certbot', 'search bot', 'SRXPT', 'SRKPT'),
('certbot_cert_bot', 'certbot', 'cert bot', 'SRTPT', 'SRTPT');

-- 4. Global Word Stats (Document Frequency across all 50 entities)
INSERT INTO global_word_stats (keyword, entity_count) VALUES 
('aditya', 2), ('alert', 1), ('analytics', 1), ('api', 2), ('approved', 1),
('async', 1), ('atom', 1), ('aur', 1), ('auth', 2), ('automation', 1),
('aws', 3), ('baas', 1), ('backend', 6), ('bldc', 1), ('blur', 1),
('broker', 1), ('bullet', 1), ('cache', 1), ('cargo', 1), ('cdn', 1),
('certificate', 1), ('clone', 1), ('compiler', 1), ('compositor', 1), ('concurrency', 1),
('config', 3), ('container', 2), ('dashboard', 1), ('dataframe', 1), ('database', 3),
('debugger', 1), ('deploy', 2), ('devops', 2), ('dns', 1), ('ee', 2),
('emulator', 1), ('endpoint', 1), ('engineer', 2), ('environment', 1), ('fan', 1),
('format', 1), ('game', 3), ('goroutine', 1), ('gpu', 1), ('hcl', 1),
('iac', 1), ('ide', 1), ('infrastructure', 2), ('item', 1), ('lab', 1),
('lead', 1), ('linux', 4), ('lua', 2), ('manager', 1), ('memory', 1),
('mentor', 1), ('metrics', 2), ('microservice', 1), ('model', 1), ('monitoring', 2),
('motor', 1), ('mutation', 1), ('new', 2), ('nginx', 1), ('notebook', 1),
('ordered', 2), ('orm', 2), ('pacman', 1), ('payload', 1), ('playbook', 1),
('postgres', 2), ('prompt', 1), ('protobuf', 1), ('proxy', 1), ('python', 3),
('queue', 1), ('remedy', 1), ('resolver', 1), ('rice', 2), ('rolling', 1),
('rpc', 1), ('rust', 3), ('sarvam', 1), ('schema', 2), ('sending', 2),
('server', 2), ('session', 1), ('shell', 1), ('shooter', 1), ('smart', 1),
('ssl', 1), ('streaming', 1), ('survival', 1), ('task', 1), ('tell', 2),
('terminal', 4), ('testing', 1), ('topic', 1), ('validation', 1), ('viking', 1),
('vim', 1), ('volume', 1), ('waf', 1), ('x11', 1);

-- 5. Context Keywords (Term Frequency)
INSERT INTO context_keywords (id, entity_id, keyword, local_frequency) VALUES 
-- Core Academic, Personal & Org
('aaditya_atom', 'aaditya', 'atom', 2), ('aaditya_item', 'aaditya', 'item', 2), ('aaditya_ee', 'aaditya', 'ee', 1), ('aaditya_new', 'aaditya', 'new', 1), ('aaditya_ordered', 'aaditya', 'ordered', 1), ('aaditya_tell', 'aaditya', 'tell', 1),
('atomberg_bldc', 'atomberg', 'bldc', 2), ('atomberg_fan', 'atomberg', 'fan', 2), ('atomberg_motor', 'atomberg', 'motor', 2), ('atomberg_smart', 'atomberg', 'smart', 2), ('atomberg_testing', 'atomberg', 'testing', 2), ('atomberg_aditya', 'atomberg', 'aditya', 1), ('atomberg_new', 'atomberg', 'new', 1), ('atomberg_ordered', 'atomberg', 'ordered', 1), ('atomberg_backend', 'atomberg', 'backend', 6),
('iitm_approved', 'iitm', 'approved', 2), ('iitm_lab', 'iitm', 'lab', 2), ('iitm_aditya', 'iitm', 'aditya', 1), ('iitm_ee', 'iitm', 'ee', 1), ('iitm_tell', 'iitm', 'tell', 1),
('savar_engineer', 'savar', 'engineer', 3), ('savar_lead', 'savar', 'lead', 2),
('saurabh_mentor', 'saurabh', 'mentor', 3), ('saurabh_manager', 'saurabh', 'manager', 2),

-- Tools & Formatting
('kivi_sarvam', 'kivi', 'sarvam', 2), ('kivi_sending', 'kivi', 'sending', 1),
('json_config', 'json', 'config', 2), ('json_format', 'json', 'format', 2), ('json_payload', 'json', 'payload', 2), ('json_sending', 'json', 'sending', 1),
('postman_api', 'postman', 'api', 3), ('postman_config', 'postman', 'config', 1),
('cognito_aws', 'cognito', 'aws', 3), ('cognito_clone', 'cognito', 'clone', 2), ('cognito_backend', 'cognito', 'backend', 2),

-- Terminal & Desktop Environment
('void_linux', 'void', 'linux', 4), ('void_rice', 'void', 'rice', 2),
('void_linux_linux', 'void_linux', 'linux', 9),
('arch_linux_pacman', 'arch_linux', 'pacman', 4), ('arch_linux_rolling', 'arch_linux', 'rolling', 3), ('arch_linux_aur', 'arch_linux', 'aur', 3),
('picom_compositor', 'picom', 'compositor', 4), ('picom_blur', 'picom', 'blur', 3), ('picom_x11', 'picom', 'x11', 3),
('wezterm_terminal', 'wezterm', 'terminal', 4), ('wezterm_emulator', 'wezterm', 'emulator', 3), ('wezterm_lua', 'wezterm', 'lua', 3),
('alacritty_terminal', 'alacritty', 'terminal', 4), ('alacritty_gpu', 'alacritty', 'gpu', 3), ('alacritty_rust', 'alacritty', 'rust', 2),
('neovim_config', 'neovim', 'config', 3), ('neovim_terminal', 'neovim', 'terminal', 2), ('neovim_vim', 'neovim', 'vim', 5), ('neovim_lua', 'neovim', 'lua', 2),
('zsh_shell', 'zsh', 'shell', 3), ('zsh_prompt', 'zsh', 'prompt', 2),
('tmux_terminal', 'tmux', 'terminal', 3), ('tmux_session', 'tmux', 'session', 3),

-- Container & Infrastructure
('docker_container', 'docker', 'container', 3), ('docker_volume', 'docker', 'volume', 2),
('kubernetes_container', 'kubernetes', 'container', 7), ('kubernetes_deploy', 'kubernetes', 'deploy', 5),
('nginx_server', 'nginx', 'server', 6), ('nginx_proxy', 'nginx', 'proxy', 4),
('terraform_infrastructure', 'terraform', 'infrastructure', 4), ('terraform_iac', 'terraform', 'iac', 4), ('terraform_hcl', 'terraform', 'hcl', 3),
('ansible_playbook', 'ansible', 'playbook', 4), ('ansible_automation', 'ansible', 'automation', 3), ('ansible_devops', 'ansible', 'devops', 3),
('cloudflare_dns', 'cloudflare', 'dns', 4), ('cloudflare_cdn', 'cloudflare', 'cdn', 3), ('cloudflare_waf', 'cloudflare', 'waf', 3),
('certbot_ssl', 'certbot', 'ssl', 4), ('certbot_certificate', 'certbot', 'certificate', 4), ('certbot_nginx', 'certbot', 'nginx', 3),

-- Observability & Messaging
('grafana_dashboard', 'grafana', 'dashboard', 5), ('grafana_metrics', 'grafana', 'metrics', 4), ('grafana_monitoring', 'grafana', 'monitoring', 3),
('prometheus_metrics', 'prometheus', 'metrics', 5), ('prometheus_alert', 'prometheus', 'alert', 3), ('prometheus_monitoring', 'prometheus', 'monitoring', 4),
('kafka_broker', 'kafka', 'broker', 4), ('kafka_streaming', 'kafka', 'streaming', 3), ('kafka_topic', 'kafka', 'topic', 4),

-- Languages & Backend
('golang_goroutine', 'golang', 'goroutine', 4), ('golang_concurrency', 'golang', 'concurrency', 3), ('golang_backend', 'golang', 'backend', 3),
('rust_compiler', 'rust', 'compiler', 4), ('rust_cargo', 'rust', 'cargo', 4), ('rust_memory', 'rust', 'memory', 3),
('grpc_protobuf', 'grpc', 'protobuf', 4), ('grpc_rpc', 'grpc', 'rpc', 4), ('grpc_microservice', 'grpc', 'microservice', 3),
('graphql_mutation', 'graphql', 'mutation', 4), ('graphql_schema', 'graphql', 'schema', 4), ('graphql_resolver', 'graphql', 'resolver', 3),
('fastapi_async', 'fastapi', 'async', 3), ('fastapi_endpoint', 'fastapi', 'endpoint', 3), ('fastapi_backend', 'fastapi', 'backend', 2),
('celery_task', 'celery', 'task', 7), ('celery_queue', 'celery', 'queue', 5),
('pydantic_validation', 'pydantic', 'validation', 4), ('pydantic_model', 'pydantic', 'model', 4), ('pydantic_schema', 'pydantic', 'schema', 3),

-- Databases & ORMs
('redis_cache', 'redis', 'cache', 8), ('redis_database', 'redis', 'database', 2), ('redis_backend', 'redis', 'backend', 1),
('dynamodb_database', 'dynamodb', 'database', 6), ('dynamodb_aws', 'dynamodb', 'aws', 8),
('diesel_orm', 'diesel', 'orm', 3), ('diesel_rust', 'diesel', 'rust', 3),
('postgresql_database', 'postgresql', 'database', 5), ('postgresql_postgres', 'postgresql', 'postgres', 4),
('supabase_postgres', 'supabase', 'postgres', 4), ('supabase_baas', 'supabase', 'baas', 4), ('supabase_auth', 'supabase', 'auth', 3),
('sqlalchemy_orm', 'sqlalchemy', 'orm', 3),

-- Data Science & Python
('pandas_dataframe', 'pandas', 'dataframe', 3), ('pandas_analytics', 'pandas', 'analytics', 2),
('conda_environment', 'conda', 'environment', 3), ('conda_python', 'conda', 'python', 2),
('jupyter_notebook', 'jupyter', 'notebook', 3), ('jupyter_python', 'jupyter', 'python', 2),
('pycharm_ide', 'pycharm', 'ide', 4), ('pycharm_python', 'pycharm', 'python', 3), ('pycharm_debugger', 'pycharm', 'debugger', 3),

-- Gaming
('efootball_game', 'efootball', 'game', 5),
('clash_royale_game', 'clash_royale', 'game', 4),
('sable_game', 'sable', 'game', 4),
('valheim_viking', 'valheim', 'viking', 4), ('valheim_survival', 'valheim', 'survival', 4), ('valheim_game', 'valheim', 'game', 3),
('max_payne_bullet', 'max_payne', 'bullet', 4), ('max_payne_shooter', 'max_payne', 'shooter', 3), ('max_payne_remedy', 'max_payne', 'remedy', 3);

-- 6. Memory Stats
INSERT INTO memory_stats (entity_id, observations_count, successful_interventions, rejected_interventions, confidence_score) VALUES 
('aaditya', 6, 5, 0, 0.88), ('atomberg', 5, 4, 0, 0.90), ('iitm', 3, 2, 0, 0.78), ('json', 3, 2, 0, 0.78),
('kivi', 2, 1, 0, 0.74), ('cognito', 4, 3, 0, 0.83), ('void', 4, 3, 0, 0.85), ('void_linux', 4, 3, 0, 0.82),
('neovim', 5, 4, 0, 0.85), ('redis', 8, 7, 1, 0.92), ('fastapi', 4, 3, 0, 0.83), ('diesel', 3, 2, 0, 0.80),
('pandas', 3, 2, 0, 0.83), ('conda', 3, 2, 0, 0.80), ('zsh', 3, 2, 0, 0.80), ('tmux', 4, 3, 0, 0.83),
('jupyter', 3, 2, 0, 0.80), ('postman', 3, 2, 0, 0.80), ('docker', 5, 4, 0, 0.88), ('postgresql', 4, 3, 0, 0.83),
('dynamodb', 5, 4, 0, 0.85), ('kubernetes', 7, 6, 0, 0.90), ('nginx', 6, 5, 0, 0.88), ('celery', 4, 2, 2, 0.70),
('sqlalchemy', 3, 2, 0, 0.78), ('efootball', 3, 2, 0, 0.78), ('clash_royale', 2, 1, 0, 0.74), ('sable', 2, 1, 0, 0.74),
('grafana', 4, 3, 0, 0.83), ('prometheus', 4, 3, 0, 0.83), ('kafka', 4, 3, 0, 0.83), ('pycharm', 3, 2, 0, 0.80),
('wezterm', 4, 3, 0, 0.83), ('alacritty', 4, 3, 0, 0.83), ('ansible', 4, 3, 0, 0.83), ('terraform', 5, 4, 0, 0.85),
('rust', 5, 4, 0, 0.85), ('golang', 4, 3, 0, 0.83), ('grpc', 4, 3, 0, 0.83), ('graphql', 4, 3, 0, 0.83),
('supabase', 4, 3, 0, 0.83), ('cloudflare', 4, 3, 0, 0.83), ('arch_linux', 5, 4, 0, 0.85), ('picom', 4, 3, 0, 0.83),
('valheim', 3, 2, 0, 0.80), ('max_payne', 3, 2, 0, 0.80), ('savar', 4, 3, 0, 0.83), ('saurabh', 4, 3, 0, 0.83),
('pydantic', 4, 3, 0, 0.83), ('certbot', 4, 3, 0, 0.83);
