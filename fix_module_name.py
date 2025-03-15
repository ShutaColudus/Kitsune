#!/usr/bin/env python3
# Kitsuneアドオンのモジュール名の問題を修正するスクリプト

import os
import sys
import shutil

print("\n===== Kitsune Module Name Fix Script =====")

# カレントディレクトリを確認
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Working directory: {current_dir}")

# ディレクトリ名を取得 (アドオンIDとして使用される)
dir_name = os.path.basename(current_dir)
print(f"Directory name (addon ID): {dir_name}")

# __init__.pyファイルを修正
init_path = os.path.join(current_dir, "__init__.py")
if os.path.exists(init_path):
    print(f"Fixing init file: {init_path}")
    
    # バックアップを作成
    backup_path = f"{init_path}.bak2"
    shutil.copy2(init_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    with open(init_path, 'r', encoding='utf-8') as f:
        init_content = f.read()
    
    # モジュール名の修正: アドオン識別子をディレクトリ名に基づいて設定
    modified_init = init_content.replace(
        'from bpy.types import AddonPreferences',
        'from bpy.types import AddonPreferences\n\n# Use directory name as addon ID\nADDON_ID = os.path.basename(os.path.dirname(__file__))\nprint(f"Addon ID: {ADDON_ID}")'
    )
    
    # 更新したファイルを保存
    with open(init_path, 'w', encoding='utf-8') as f:
        f.write(modified_init)
    print(f"✓ Updated {init_path} with dynamic module name detection")

# preferences.pyファイルを修正
pref_path = os.path.join(current_dir, "preferences.py")
if os.path.exists(pref_path):
    print(f"Fixing preferences file: {pref_path}")
    
    # バックアップを作成
    backup_path = f"{pref_path}.bak"
    shutil.copy2(pref_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    with open(pref_path, 'r', encoding='utf-8') as f:
        pref_content = f.read()
    
    # モジュール名の修正: 動的にアドオンIDを設定
    if 'bl_idname = "kitsune"' in pref_content:
        modified_pref = pref_content.replace(
            'bl_idname = "kitsune"',
            'bl_idname = __package__  # Use package name instead of hardcoded string'
        )
        
        # 更新したファイルを保存
        with open(pref_path, 'w', encoding='utf-8') as f:
            f.write(modified_pref)
        print(f"✓ Updated {pref_path} with dynamic module name")
    else:
        print("! Could not find hardcoded addon ID in preferences.py")

# get_active_provider関数も修正
if os.path.exists(pref_path):
    with open(pref_path, 'r', encoding='utf-8') as f:
        pref_content = f.read()
    
    # 動的にアドオンIDを取得する方法に修正
    if 'preferences = bpy.context.preferences.addons["kitsune"].preferences' in pref_content:
        modified_pref = pref_content.replace(
            'preferences = bpy.context.preferences.addons["kitsune"].preferences',
            'preferences = bpy.context.preferences.addons[__package__].preferences'
        )
        
        # 更新したファイルを保存
        with open(pref_path, 'w', encoding='utf-8') as f:
            f.write(modified_pref)
        print(f"✓ Updated get_active_provider in {pref_path} to use dynamic module name")
    else:
        print("! Could not find get_active_provider hardcoded addon ID")

# ui.pyファイルを修正
ui_path = os.path.join(current_dir, "ui.py")
if os.path.exists(ui_path):
    print(f"Fixing UI file: {ui_path}")
    
    # バックアップを作成
    backup_path = f"{ui_path}.bak2"
    shutil.copy2(ui_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    with open(ui_path, 'r', encoding='utf-8') as f:
        ui_content = f.read()
    
    # 修正: 固定アドオン名の参照を動的に
    ui_content = ui_content.replace(
        'preferences = context.preferences.addons["kitsune"].preferences',
        'preferences = context.preferences.addons[__package__].preferences'
    )
    
    # 更新したファイルを保存
    with open(ui_path, 'w', encoding='utf-8') as f:
        f.write(ui_content)
    print(f"✓ Updated {ui_path} with dynamic module name references")

# check_ui_properties.pyも修正
check_path = os.path.join(current_dir, "check_ui_properties.py")
if os.path.exists(check_path):
    print(f"Fixing check script: {check_path}")
    
    # バックアップを作成
    backup_path = f"{check_path}.bak"
    shutil.copy2(check_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    with open(check_path, 'r', encoding='utf-8') as f:
        check_content = f.read()
    
    # 修正: アドオン検出を動的に
    modified_check = check_content.replace(
        'if "kitsune" not in bpy.context.preferences.addons:',
        'addon_id = os.path.basename(os.path.dirname(__file__))\nprint(f"Checking for addon ID: {addon_id}")\nif addon_id not in bpy.context.preferences.addons:'
    )
    
    modified_check = modified_check.replace(
        'prefs = bpy.context.preferences.addons["kitsune"].preferences',
        'prefs = bpy.context.preferences.addons[addon_id].preferences'
    )
    
    # 更新したファイルを保存
    with open(check_path, 'w', encoding='utf-8') as f:
        f.write(modified_check)
    print(f"✓ Updated {check_path} with dynamic addon detection")

print("\n===== Fix Complete =====")
print("\nPlease follow these steps to complete the fix:")
print("1. Restart Blender")
print("2. Disable the Kitsune addon (Edit > Preferences > Add-ons)")
print("3. Enable the Kitsune addon again")
print("4. The addon should now load correctly without 'bpy_prop_c...kitsune not found' errors")
print("\nIf you still experience issues, please report them.")