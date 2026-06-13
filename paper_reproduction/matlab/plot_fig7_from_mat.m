function plot_fig7_from_mat(data_root, traj, v_max, out_png)
% Plot Fig.7-style XY trajectory comparison from archived .mat files.
%
% traj: 'circle' or 'lemniscate'
% v_max: e.g. 10.0
%
% Example:
%   plot_fig7_from_mat('../data/mat', 'circle', 10.0, '../data/results/fig7_circle.png')

if nargin < 1 || isempty(data_root)
    data_root = '../data/mat';
end
if nargin < 2 || isempty(traj)
    traj = 'circle';
end
if nargin < 3 || isempty(v_max)
    v_max = 10.0;
end
if nargin < 4 || isempty(out_png)
    out_png = sprintf('../data/results/fig7_%s_v%.1f.png', traj, v_max);
end

algo_order = {'nominal', 'gpmpc', 'ssi'};
labels = {'Nominal MPC', 'GP-MPC', 'Ours'};
colors = [0.4660 0.6740 0.1880; 0.6350 0.0780 0.1840; 0 0.4470 0.7410];

ref_x = [];
figure('Color', 'w');
hold on;

for i = 1:numel(algo_order)
    mat_file = fullfile(data_root, algo_order{i}, traj, sprintf('trial01_v%.1f.mat', v_max));
    if ~isfile(mat_file)
        warning('Missing file: %s', mat_file);
        continue;
    end
    S = load(mat_file);
    if isempty(ref_x)
        ref_x = S.ref_x;
        plot(ref_x(:, 1), ref_x(:, 2), 'k-', 'LineWidth', 1.5, 'DisplayName', 'Reference');
    end
    x = S.x;
    n = min(size(x, 1), size(ref_x, 1));
    t_start = max(1, floor(0.4 * n));
    t_end = max(t_start + 1, floor(0.5 * n));
    plot(x(t_start:t_end, 1), x(t_start:t_end, 2), '-', 'Color', colors(i, :), ...
        'LineWidth', 1.5, 'DisplayName', labels{i});
end

grid on;
xlabel('x (m)');
ylabel('y (m)');
title(sprintf('Fig.7-style segment | %s | v=%.1f', traj, v_max));
legend('Location', 'best');
saveas(gcf, out_png);
fprintf('Saved figure to %s\n', out_png);

end
