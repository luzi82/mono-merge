#!/usr/bin/env python3

import argparse
import csv


def main():
    parser = argparse.ArgumentParser(
        description='Create cmap proxy glyphs for glyphs that are both in cmap and referenced by composites'
    )
    parser.add_argument('input_codepoint_csv', help='Input codepoint CSV file')
    parser.add_argument('input_glyph_csv', help='Input glyph CSV file')
    parser.add_argument('output_cmapproxy_csv', help='Output CSV containing glyph index mapping')
    parser.add_argument('output_codepoint_csv', help='Output codepoint CSV file')
    parser.add_argument('output_glyph_csv', help='Output glyph CSV file')
    
    args = parser.parse_args()
    
    # First pass: read glyph CSV and create index mapping
    glyph_index_map = {}  # Maps old glyph_index to new glyph_index
    glyph_rows = []
    changed_glyphs = []
    next_glyph_index = 0
    
    with open(args.input_glyph_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        # First pass: count existing glyphs and collect rows that need proxy
        rows_needing_proxy = []
        for row in reader:
            glyph_index = int(row['glyph_index'])
            cmap_used = int(row.get('cmap_used', 0))
            glyf_used = int(row.get('glyf_used', 0))
            next_glyph_index = max(next_glyph_index, glyph_index + 1)
            
            if cmap_used >= 1 and glyf_used >= 1:
                rows_needing_proxy.append(row)
            else:
                glyph_rows.append(row)
                glyph_index_map[glyph_index] = glyph_index
        
        # Second pass: create proxy glyphs starting from next_glyph_index
        for row in rows_needing_proxy:
            old_glyph_index = int(row['glyph_index'])
            cmap_used = int(row.get('cmap_used', 0))
            glyf_used = int(row.get('glyf_used', 0))
            new_glyph_index = next_glyph_index
            next_glyph_index += 1
            
            # Create a new row for the cmap proxy glyph
            new_row = row.copy()
            new_row['glyph_index'] = str(new_glyph_index)
            new_row['glyf_used'] = '0'
            new_row['num_glyph'] = '1'
            new_row['is_composite'] = 'True'
            new_row['num_contours'] = '-1'
            glyph_rows.append(new_row)
            
            # Update the original row to set cmap_used = 0 and increment glyf_used
            row['cmap_used'] = '0'
            row['glyf_used'] = str(glyf_used + 1)
            glyph_rows.append(row)
            
            # Track the mapping
            glyph_index_map[old_glyph_index] = new_glyph_index
            changed_glyphs.append({
                'old_glyph_index': old_glyph_index,
                'new_glyph_index': new_glyph_index
            })
    
    # Sort glyph_rows by glyph_index
    glyph_rows.sort(key=lambda row: int(row['glyph_index']))
    
    # Write output glyph CSV
    with open(args.output_glyph_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(glyph_rows)
    
    # Process codepoint CSV and update glyph_index based on mapping
    with open(args.input_codepoint_csv, 'r', newline='', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        codepoint_fieldnames = reader.fieldnames
        
        with open(args.output_codepoint_csv, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=codepoint_fieldnames)
            writer.writeheader()
            
            for row in reader:
                old_glyph_index = int(row['glyph_index'])
                # Look up the new glyph_index from the mapping
                new_glyph_index = glyph_index_map.get(old_glyph_index, old_glyph_index)
                # Update glyph_index with new value
                row['glyph_index'] = str(new_glyph_index)
                
                # If this glyph was remapped, update composite info
                if new_glyph_index != old_glyph_index:
                    row['is_composite'] = 'True'
                    row['num_contours'] = '-1'
                    row['glyf_used'] = '0'
                    row['num_glyph'] = '1'
                
                writer.writerow(row)
    
    # Write output_cmapproxy_csv containing only changed glyph indices
    with open(args.output_cmapproxy_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['old_glyph_index', 'new_glyph_index'])
        writer.writeheader()
        writer.writerows(changed_glyphs)


if __name__ == '__main__':
    main()
