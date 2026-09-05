-- seeds/default.sql

-- 1. System Stats (Total Entities: 18)
INSERT OR REPLACE INTO system_stats (id, total_entities) VALUES (1, 18);

-- 2. Canonical Entities
INSERT INTO entities (id, canonical_form, entity_type, primary_metaphone, secondary_metaphone) VALUES 
('aaditya', 'Aaditya', 'PERSON', 'ATT', 'ATT'),
('atomberg', 'Atomberg', 'ORG', 'ATMP', 'ATMP'),
('iitm', 'IITM', 'ORG', 'ATM', 'ATM'),
('json', 'JSON', 'TECH_TERM', 'JSN', 'ASN'),
('kivi', 'Kivi', 'TECH_TERM', 'KF', 'KF'),
('cognito', 'Cognito', 'TECH_TERM', 'KNT', 'KKNT'),
('void', 'Void', 'TECH_TERM', 'FT', 'FT'),
('neovim', 'Neovim', 'TECH_TERM', 'NFM', 'NFM'),
('redis', 'Redis', 'TECH_TERM', 'RTS', 'RTS'),
('fastapi', 'FastAPI', 'TECH_TERM', 'FSTP', 'FSTP'),
('diesel', 'Diesel', 'TECH_TERM', 'TSL', 'TSL'),
('pandas', 'Pandas', 'TECH_TERM', 'PNTS', 'PNTS'),
('conda', 'Conda', 'TECH_TERM', 'KNT', 'KNT'),
('zsh', 'Zsh', 'TECH_TERM', 'S', 'S'),
('tmux', 'Tmux', 'TECH_TERM', 'TMKS', 'TMKS'),
('jupyter', 'Jupyter', 'TECH_TERM', 'JPTR', 'YPTR'),
('postman', 'Postman', 'TECH_TERM', 'PSTMN', 'PSTMN'),
('docker', 'Docker', 'TECH_TERM', 'TKR', 'TKR');

-- 3. Phonetic Aliases
INSERT INTO phonetic_aliases (id, entity_id, alias, primary_metaphone, secondary_metaphone) VALUES 
('aaditya_aditya', 'aaditya', 'aditya', 'ATT', 'ATT'),
('atomberg_atom_berg', 'atomberg', 'atom berg', 'ATMP', 'ATMP'),
('iitm_item', 'iitm', 'item', 'ATM', 'ATM'),
('json_jason', 'json', 'jason', 'JSN', 'ASN'),
('kivi_keevee', 'kivi', 'keevee', 'KF', 'KF'),
('cognito_incognito', 'cognito', 'incognito', 'ANKN', 'ANKN'),
('void_avoid', 'void', 'avoid', 'AFT', 'AFT'),
('neovim_neo_them', 'neovim', 'neo them', 'N0M', 'N0M'),
('redis_read_is', 'redis', 'read is', 'RTS', 'RTS'),
('fastapi_fast_api', 'fastapi', 'fast api', 'FSTP', 'FSTP'),
('diesel_dezel', 'diesel', 'dezel', 'TSL', 'TSL'),
('pandas_pan_das', 'pandas', 'pan das', 'PNTS', 'PNTS'),
('conda_corner', 'conda', 'corner', 'KRNR', 'KRNR'),
('zsh_z_shell', 'zsh', 'z shell', 'SLL', 'SLL'),
('tmux_tea_max', 'tmux', 'tea max', 'TMKS', 'TMKS'),
('jupyter_jewel_iter', 'jupyter', 'jewel iter', 'JLTR', 'YLTR'),
('postman_post_man', 'postman', 'post man', 'PSTMN', 'PSTMN'),
('docker_dock_her', 'docker', 'dock her', 'TKHR', 'TKHR');

-- 4. Global Word Stats (Document Frequency)
INSERT INTO global_word_stats (keyword, entity_count) VALUES 
('atom', 1), ('item', 1), ('ee', 2), ('new', 2), ('ordered', 2), ('tell', 2), 
('bldc', 1), ('fan', 1), ('motor', 1), ('smart', 1), ('testing', 1), 
('aditya', 2), ('approved', 2), ('lab', 1), ('config', 3), ('format', 1), 
('payload', 1), ('sending', 2), ('sarvam', 1), ('aws', 1), ('clone', 1), 
('backend', 3), ('linux', 1), ('rice', 1), ('terminal', 2),
-- New entity keywords
('cache', 1), ('database', 1), ('async', 1), ('endpoint', 1), 
('orm', 1), ('rust', 1), ('dataframe', 1), ('analytics', 1), 
('environment', 1), ('python', 1), ('shell', 1), ('prompt', 1), 
('session', 1), ('notebook', 1), ('api', 1), ('container', 1), ('volume', 1);

-- 5. Context Keywords (Term Frequency)
INSERT INTO context_keywords (id, entity_id, keyword, local_frequency) VALUES 
-- Original Contexts (Aaditya through Neovim)
('aaditya_atom', 'aaditya', 'atom', 2), ('aaditya_item', 'aaditya', 'item', 2), ('aaditya_ee', 'aaditya', 'ee', 1), ('aaditya_new', 'aaditya', 'new', 1), ('aaditya_ordered', 'aaditya', 'ordered', 1), ('aaditya_tell', 'aaditya', 'tell', 1),
('atomberg_bldc', 'atomberg', 'bldc', 2), ('atomberg_fan', 'atomberg', 'fan', 2), ('atomberg_motor', 'atomberg', 'motor', 2), ('atomberg_smart', 'atomberg', 'smart', 2), ('atomberg_testing', 'atomberg', 'testing', 2), ('atomberg_aditya', 'atomberg', 'aditya', 1), ('atomberg_new', 'atomberg', 'new', 1), ('atomberg_ordered', 'atomberg', 'ordered', 1), ('atomberg_backend', 'atomberg', 'backend', 3),
('iitm_approved', 'iitm', 'approved', 2), ('iitm_lab', 'iitm', 'lab', 2), ('iitm_aditya', 'iitm', 'aditya', 1), ('iitm_ee', 'iitm', 'ee', 1), ('iitm_tell', 'iitm', 'tell', 1),
('json_config', 'json', 'config', 2), ('json_format', 'json', 'format', 2), ('json_payload', 'json', 'payload', 2), ('json_sending', 'json', 'sending', 1),
('kivi_sarvam', 'kivi', 'sarvam', 2), ('kivi_sending', 'kivi', 'sending', 1),
('cognito_aws', 'cognito', 'aws', 3), ('cognito_clone', 'cognito', 'clone', 2), ('cognito_backend', 'cognito', 'backend', 2),
('void_linux', 'void', 'linux', 4), ('void_rice', 'void', 'rice', 2),
('neovim_config', 'neovim', 'config', 3), ('neovim_terminal', 'neovim', 'terminal', 2),

-- New Real-World Entity Contexts
('redis_cache', 'redis', 'cache', 3), ('redis_database', 'redis', 'database', 2), ('redis_backend', 'redis', 'backend', 1),
('fastapi_async', 'fastapi', 'async', 3), ('fastapi_endpoint', 'fastapi', 'endpoint', 3),
('diesel_orm', 'diesel', 'orm', 3), ('diesel_rust', 'diesel', 'rust', 3),
('pandas_dataframe', 'pandas', 'dataframe', 3), ('pandas_analytics', 'pandas', 'analytics', 2),
('conda_environment', 'conda', 'environment', 3), ('conda_python', 'conda', 'python', 2),
('zsh_shell', 'zsh', 'shell', 3), ('zsh_prompt', 'zsh', 'prompt', 2),
('tmux_terminal', 'tmux', 'terminal', 3), ('tmux_session', 'tmux', 'session', 3),
('jupyter_notebook', 'jupyter', 'notebook', 3), ('jupyter_python', 'jupyter', 'python', 2),
('postman_api', 'postman', 'api', 3), ('postman_config', 'postman', 'config', 1),
('docker_container', 'docker', 'container', 3), ('docker_volume', 'docker', 'volume', 2);

-- 6. Memory Stats
INSERT INTO memory_stats (entity_id, observations_count, confidence_score) VALUES 
('aaditya', 2, 0.78), ('atomberg', 5, 0.90), ('iitm', 1, 0.70), ('json', 1, 0.70), 
('kivi', 1, 0.70), ('cognito', 3, 0.83), ('void', 4, 0.88), ('neovim', 3, 0.83),
('redis', 3, 0.83), ('fastapi', 3, 0.83), ('diesel', 3, 0.83), ('pandas', 3, 0.83), 
('conda', 3, 0.83), ('zsh', 3, 0.83), ('tmux', 3, 0.83), ('jupyter', 3, 0.83), 
('postman', 3, 0.83), ('docker', 3, 0.83);
