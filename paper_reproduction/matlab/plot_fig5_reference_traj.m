function plot_fig5_reference_traj(data_root, out_dir)
% Plot Fig.5-style 3D reference trajectories from archived SSI-MPC mat files.
%
% Example:
%   plot_fig5_reference_traj('../data/mat', '../data/results')

if nargin < 1 || isempty(data_root)
    data_root = '../data/mat';
end
if nargin < 2 || isempty(out_dir)
    out_dir = '../data/results';
end

trajs = {'circle', 'wrapped_circle', 'lemniscate', 'wrapped_lemniscate'};
for i = 1:numel(trajs)
    mat_file = fullfile(data_root, 'ssi', trajs{i}, 'trial01_v10.0.mat');
    if ~isfile(mat_file)
        warning('Skip %s (missing %s)', trajs{i}, mat_file);
        continue;
    end
    S = load(mat_file);
    ref_x = S.ref_x;
    figure('Color', 'w');
    plot3(ref_x(:, 1), ref_x(:, 2), ref_x(:, 3), 'b-', 'LineWidth', 1.5); hold on;
    plot3(ref_x(:, 1), ref_x(:, 2), zeros(size(ref_x, 3)), 'Color', [0.7 0.7 0.7], 'LineWidth', 1.0);
    grid on;
    xlabel('x (m)'); ylabel('y (m)'); zlabel('z (m)');
    title(strrep(trajs{i}, '_', ' '));
    out_png = fullfile(out_dir, sprintf('fig5_%s.png', trajs{i}));
    saveas(gcf, out_png);
    fprintf('Saved %s\n', out_png);
end

end
