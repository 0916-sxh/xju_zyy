function plot_fig6_from_records(records_csv, out_png)
% Plot Fig.6-style RMSE curves from paper_reproduction/data/results/fig6_summary.csv
%
% Example:
%   cd /home/sxh/zyy_ws/src/paper_reproduction/matlab
%   plot_fig6_from_records('../data/results/fig6_summary.csv', '../data/results/fig6_plot.png')

if nargin < 1 || isempty(records_csv)
    records_csv = '../data/results/fig6_summary.csv';
end
if nargin < 2 || isempty(out_png)
    out_png = '../data/results/fig6_plot.png';
end

T = readtable(records_csv, 'TextType', 'string');
trajs = unique(T.trajectory, 'stable');
algos = ["nominal", "ssi", "gpmpc"];
algo_labels = ["Nominal MPC", "Ours", "GP-MPC"];
colors = [0.4660 0.6740 0.1880; 0 0.4470 0.7410; 0.6350 0.0780 0.1840];
markers = {'s', '^', 'o'};

figure('Color', 'w');
tiledlayout(2, 2);

for ti = 1:numel(trajs)
    nexttile;
    hold on;
    traj = trajs(ti);
    for ai = 1:numel(algos)
        idx = T.trajectory == traj & T.algorithm == algos(ai);
        if ~any(idx)
            continue;
        end
        sub = sortrows(T(idx, :), 'v_max');
        errorbar(sub.v_max, sub.rmse_mean, sub.rmse_std, markers{ai}, ...
            'Color', colors(ai, :), 'LineWidth', 1.5, 'DisplayName', algo_labels(ai));
    end
    grid on;
    xlabel('Configured v_{max} (m/s)');
    ylabel('RMSE (m)');
    title(strrep(char(traj), '_', ' '));
    legend('Location', 'northwest');
end

saveas(gcf, out_png);
fprintf('Saved figure to %s\n', out_png);

end
