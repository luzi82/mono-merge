#!/usr/bin/env python3

import argparse
import csv


def main():
    parser = argparse.ArgumentParser(
        description='Add new_glyph_name column to glyph and codepoint CSV files based on cmap_used and glyf_used'
    )
    parser.add_argument('input_codepoint_csv', help='Input codepoint CSV file')
    parser.add_argument('input_glyph_csv', help='Input glyph CSV file')
    parser.add_argument('output_cmapproxy_csv', help='Output CSV containing only changed glyph names')
    parser.add_argument('output_codepoint_csv', help='Output codepoint CSV file')
    parser.add_argument('output_glyph_csv', help='Output glyph CSV file')
    
    args = parser.parse_args()
    
    # First pass: read glyph CSV and create mapping with new_glyph_name
    glyph_name_map = {}
    glyph_rows = []
    changed_glyphs = []
    
    with open(args.input_glyph_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            glyph_name = row['glyph_name']
            cmap_used = int(row.get('cmap_used', 0))
            glyf_used = int(row.get('glyf_used', 0))
            
            # Determine new_glyph_name based on conditions
            if cmap_used >= 1 and glyf_used >= 1:
                new_glyph_name = glyph_name + '.cmapproxy'
                
                # Create a new row for the .cmapproxy glyph
                new_row = row.copy()
                new_row['glyph_name'] = new_glyph_name
                new_row['glyf_used'] = '0'
                new_row['num_glyph'] = '1'
                new_row['is_composite'] = 'True'
                new_row['num_contours'] = '-1'
                glyph_rows.append(new_row)
                
                # Update the original row to set cmap_used = 0 and increment glyf_used
                row['cmap_used'] = '0'
                row['glyf_used'] = str(glyf_used + 1)
                glyph_rows.append(row)
                
                # Track changed glyphs
                changed_glyphs.append({
                    'old_glyph_name': glyph_name,
                    'new_glyph_name': new_glyph_name
                })
            else:
                new_glyph_name = glyph_name
                glyph_rows.append(row)
            
            glyph_name_map[glyph_name] = new_glyph_name
    
    # Sort glyph_rows by glyph_name
    glyph_rows.sort(key=lambda row: row['glyph_name'])
    
    # Write output glyph CSV without new_glyph_name column
    with open(args.output_glyph_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(glyph_rows)
    
    # Process codepoint CSV and update glyph_name to new_glyph_name
    with open(args.input_codepoint_csv, 'r', newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        codepoint_fieldnames = reader.fieldnames
        
        with open(args.output_codepoint_csv, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=codepoint_fieldnames)
            writer.writeheader()
            
            for row in reader:
                glyph_name = row['glyph_name']
                # Look up the new_glyph_name from the glyph mapping
                new_glyph_name = glyph_name_map.get(glyph_name, glyph_name)
                # Update glyph_name with new_glyph_name
                row['glyph_name'] = new_glyph_name
                
                # If this is a cmapproxy replaced row, update composite info
                if new_glyph_name != glyph_name:
                    row['is_composite'] = 'True'
                    row['num_contours'] = '-1'
                    row['glyf_used'] = '0'
                    row['num_glyph'] = '1'
                
                writer.writerow(row)
    
    # Write output_cmapproxy_csv containing only changed glyphs
    with open(args.output_cmapproxy_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['old_glyph_name', 'new_glyph_name'])
        writer.writeheader()
        writer.writerows(changed_glyphs)


if __name__ == '__main__':
    main()
