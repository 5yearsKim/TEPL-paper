#!/usr/bin/env python3
"""Plot certified dot-chain phase costs and transpose rank side by side."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import ScalarFormatter, MaxNLocator

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, default=ROOT / 'evaluation/certified-scalability/performance_summary.json')
    args = parser.parse_args()
    data = json.loads(args.results.read_text())
    if data['backend'] != 'certified':
        raise ValueError('expected certified measurements')
    rows = data['cases']
    if len(rows) != 15 or any(r['status'] != 'accepted' for r in rows):
        raise ValueError('expected all 15 original automatic configurations')
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': ['Arimo', 'DejaVu Sans'],
        'font.size': 8, 'axes.titlesize': 9, 'axes.labelsize': 8,
        'xtick.labelsize': 7, 'ytick.labelsize': 7, 'pdf.fonttype': 42,
        'axes.spines.top': False, 'axes.spines.right': False,
    })
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.95))
    fig.subplots_adjust(left=.075, right=.985, bottom=.26, top=.85, wspace=.35)
    color = '#356B8C'
    for ax, family, title in zip(axes[1:], ['rank'], ['(b) Transpose rank']):
        group = sorted((r for r in rows if r['family'] == family), key=lambda r: r['size'])
        x = [r['size'] for r in group]
        y = [r['median_total_ms'] for r in group]
        ax.errorbar(x, y,
                    yerr=[[r['median_total_ms'] - r['min_total_ms'] for r in group],
                          [r['max_total_ms'] - r['median_total_ms'] for r in group]],
                    color=color, marker='o', markersize=3, linewidth=1.2,
                    elinewidth=.65, capsize=2)
        ax.set_ylim(bottom=0)
        ax.set_ylabel('Compile time (ms)')
        ax.set_title(title, loc='left', pad=10)
        if family == 'chain':
            ax.set_xticks([1, 3, 5, 7, 10])
            ax.set_xlabel('Dots per side')
        else:
            ax.set_xscale('log', base=2)
            ax.set_xticks([2, 4, 8, 16, 32])
            ax.xaxis.set_major_formatter(ScalarFormatter())
            ax.set_xlabel('Tensor rank')
    ax = axes[0]
    chains = sorted((r for r in rows if r['family'] == 'chain'), key=lambda r: r['size'])
    bottom = np.zeros(len(chains))
    for field, label, fill in [
        ('preparation_ms', 'Prepare', '#5479A8'),
        ('certification_ms', 'Certify / construct', '#6A9F88'),
        ('lowering_ms', 'Lower / validate', '#D4A65C'),
        ('other_ms', 'Other', '#A7B2BB'),
    ]:
        values = np.array([r['mean_' + field] for r in chains])
        ax.bar([r['size'] for r in chains], values, bottom=bottom, width=.74,
               color=fill, label=label, linewidth=0)
        bottom += values
    if not np.allclose(bottom, [r['mean_total_ms'] for r in chains], rtol=1e-12, atol=1e-12):
        raise ValueError('phase means do not add to total')
    ax.errorbar([r['size'] for r in chains],
                [r['median_total_ms'] for r in chains],
                yerr=[[r['median_total_ms'] - r['min_total_ms'] for r in chains],
                      [r['max_total_ms'] - r['median_total_ms'] for r in chains]],
                color='#263238', marker='o', markersize=3, linewidth=1,
                elinewidth=.65, capsize=2, label='Median total', zorder=3)
    ax.set_title('(a) Dot chain and phase cost', loc='left', pad=10)
    ax.set_xticks([1, 3, 5, 7, 10])
    ax.set_xlabel('Dots per side')
    ax.set_ylabel('Compile time (ms)')
    for ax in axes:
        ax.grid(axis='y', alpha=.2, linewidth=.6)
        ax.set_axisbelow(True)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    axes[0].set_ylim(bottom=0)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(.5, .015),
               ncol=5, frameon=False, fontsize=7, handlelength=1.3, columnspacing=1.6)
    out = args.results.parent / 'figures'
    out.mkdir(exist_ok=True)
    for suffix in ('pdf', 'svg', 'png'):
        fig.savefig(out / ('scalability.' + suffix), dpi=220)
    fig.savefig(ROOT / 'figures/scalability.pdf')
    plt.close(fig)
    print(out / 'scalability.pdf')


if __name__ == '__main__':
    main()
